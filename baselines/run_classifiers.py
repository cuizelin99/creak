import logging
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

import datasets
import numpy as np
from datasets import load_dataset, load_metric

import transformers
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    EvalPrediction,
    HfArgumentParser,
    Trainer,
    TrainingArguments,
    default_data_collator,
    set_seed,
)
from transformers.trainer_utils import get_last_checkpoint

logger = logging.getLogger(__name__)


@dataclass
class DataTrainingArguments:
    """
    Arguments pertaining to the train/dev/test datasets.
    """

    train_path: Optional[str] = field(
        default=None,
        metadata={"help": "Path to training set"},
    )
    dev_path: Optional[str] = field(
        default=None,
        metadata={"help": "Path to validation set"},
    )
    test_path: Optional[str] = field(
        default=None,
        metadata={"help": "Path to test set"},
    )
    contra_path: Optional[str] = field(
        default=None,
        metadata={"help": "Path to contrastive set"},
    )
    input_mod: Optional[str] = field(
        default=None,
        metadata={
            "help": "if set to 'dpr' append top k articles (k set by topk argument). if set to 'no_ent' mask out all entities"},
    )
    topk: Optional[int] = field(
        default=3,
        metadata={"help": "number or articles to append if input_mod='dpr'"},
    )
    max_train_samples: Optional[int] = field(
        default=None,
        metadata={
            "help": "For debugging purposes or quicker training, truncate the number of training examples to this value if set"},
    )
    max_eval_samples: Optional[int] = field(
        default=None,
        metadata={
            "help": "For debugging purposes or quicker training, truncate the number of evaluation examples to this value if set"},
    )
    max_predict_samples: Optional[int] = field(
        default=None,
        metadata={
            "help": "For debugging purposes or quicker training, truncate the number of prediction examples to this value if set"},
    )
    max_seq_length: Optional[int] = field(
        default=512,
        metadata={
            "help": "The maximum total input sequence length after tokenization. Sequences longer "
                    "than this will be truncated, sequences shorter will be padded."
        },
    )


@dataclass
class ModelArguments:
    """
    Arguments pertaining to which model/config/tokenizer we are going to fine-tune from.
    """

    model_name_or_path: str = field(
        default=None, metadata={
            "help": "Path to pretrained model or model identifier from huggingface.co/models"}
    )
    config_name: Optional[str] = field(
        default=None, metadata={
            "help": "Pretrained config name or path if not the same as model_name"}
    )
    do_lower_case: Optional[bool] = field(
        default=False,
        metadata={
            "help": "arg to indicate if tokenizer should do lower case in AutoTokenizer.from_pretrained()"},
    )
    use_fast_tokenizer: bool = field(
        default=True,
        metadata={
            "help": "Whether to use one of the fast tokenizer (backed by the tokenizers library) or not."},
    )


def main():
    # See all possible arguments in src/transformers/training_args.py
    # or by passing the --help flag to this script.
    # We now keep distinct sets of args, for a cleaner separation of concerns.

    parser = HfArgumentParser(
        (ModelArguments, DataTrainingArguments, TrainingArguments))
    model_args, data_args, training_args = parser.parse_args_into_dataclasses()

    # Setup logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.warning(
        f"Process rank: {training_args.local_rank}, device: {training_args.device}, n_gpu: {training_args.n_gpu} "
        + f"distributed training: {bool(training_args.local_rank != -1)}, 16-bits training: {training_args.fp16}"
    )
    logger.info(f"Model parameters {model_args}")
    logger.info(f"Training/evaluation parameters {training_args}")

    # Detecting last checkpoint.
    last_checkpoint = None
    if os.path.isdir(
            training_args.output_dir) and training_args.do_train and not training_args.overwrite_output_dir:
        last_checkpoint = get_last_checkpoint(training_args.output_dir)
        if last_checkpoint is None and len(
                os.listdir(training_args.output_dir)) > 0:
            raise ValueError(
                f"Output directory ({training_args.output_dir}) already exists and is not empty. "
                "Use --overwrite_output_dir to overcome."
            )
        elif last_checkpoint is not None:
            logger.info(
                f"Checkpoint detected, resuming training at {last_checkpoint}. To avoid this behavior, change "
                "the `--output_dir` or add `--overwrite_output_dir` to train from scratch."
            )

    # Set seed before initializing model.
    set_seed(training_args.seed)

    # Loading Entity Commonsense Dataset
    if training_args.do_train:
        train_dataset = load_dataset("json", data_files=data_args.train_path,
                                     split="train")

    if training_args.do_eval:
        eval_dataset = load_dataset("json", data_files=data_args.dev_path,
                                    split="train")

    if training_args.do_predict:
        test_dataset = load_dataset("json", data_files=data_args.test_path,
                                    split="train")
        contra_dataset = load_dataset("json", data_files=data_args.contra_path,
                                      split="train")

    # Labels (Binary Classification)
    label2id = {'true': 1, 'false': 0}
    id2label = {v: k for k, v in label2id.items()}
    num_labels = len(label2id)

    # Setting up model and tokenizer configs
    config = AutoConfig.from_pretrained(
        model_args.config_name if model_args.config_name else model_args.model_name_or_path,
        num_labels=num_labels,
        finetuning_task="xnli",
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        model_args.model_name_or_path,
        config=config,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name_or_path,
        do_lower_case=model_args.do_lower_case,
        use_fast=model_args.use_fast_tokenizer,
    )

    # Preprocess train/dev/test sets
    def preprocess_vanilla(examples):
        # Tokenize the texts
        return tokenizer(
            examples["sentence"],
            padding="max_length",
            max_length=data_args.max_seq_length,
            truncation=True,
        )

    def preprocess_no_ent(examples):
        # Tokenize the texts
        no_ent_inputs = []
        for sent, ent_locs in zip(examples["sentence"],
                                  examples['entity_mention_loc']):
            prev_e = 0
            no_ent_sent = ''
            for cur_s, cur_e in ent_locs:
                no_ent_sent = no_ent_sent + sent[
                                            prev_e:cur_s] + tokenizer.mask_token
                prev_e = cur_e
            no_ent_sent = no_ent_sent + sent[prev_e:]
            no_ent_inputs.append(no_ent_sent)
        return tokenizer(
            no_ent_inputs,
            padding="max_length",
            max_length=data_args.max_seq_length,
            truncation=True,
        )

    def preprocess_dpr(examples):
        # Tokenize the texts
        dpr_inputs = [f' {tokenizer.sep_token} '.join(
            [sent] + [p['text'] for p in passages[:data_args.topk]])
                      for sent, passages in
                      zip(examples['sentence'], examples['dpr'])]
        return tokenizer(
            dpr_inputs,
            padding="max_length",
            max_length=data_args.max_seq_length,
            truncation=True,
        )

    if data_args.input_mod == 'dpr':
        preprocess_function = preprocess_dpr
    elif data_args.input_mod == 'no_ent':
        preprocess_function = preprocess_no_ent
    elif data_args.input_mod is None:
        preprocess_function = preprocess_vanilla
    else:
        exit()

    if training_args.do_train:
        if data_args.max_train_samples is not None:
            train_dataset = train_dataset.select(
                range(data_args.max_train_samples))
        with training_args.main_process_first(
                desc="train dataset map pre-processing"):
            train_dataset = train_dataset.map(
                lambda ex: {'label': label2id[ex['label']]})
            train_dataset = train_dataset.map(
                preprocess_function,
                batched=True,
                desc="Running tokenizer on train dataset",
            )
            columns_to_return = ['input_ids', 'label', 'attention_mask']
            train_dataset.set_format(type='torch', columns=columns_to_return)
        # Log a few random samples from the training set:
        for index in random.sample(range(len(train_dataset)), 3):
            logger.info(
                f"Sample {index} of the training set: {train_dataset[index]}.")

    if training_args.do_eval:
        if data_args.max_eval_samples is not None:
            eval_dataset = eval_dataset.select(
                range(data_args.max_eval_samples))
        with training_args.main_process_first(
                desc="validation dataset map pre-processing"):
            eval_dataset = eval_dataset.map(
                lambda ex: {'label': label2id[ex['label']]})
            eval_dataset = eval_dataset.map(
                preprocess_function,
                batched=True,
                desc="Running tokenizer on validation dataset",
            )
            columns_to_return = ['input_ids', 'label', 'attention_mask']
            eval_dataset.set_format(type='torch', columns=columns_to_return)

    if training_args.do_predict:
        if data_args.max_predict_samples is not None:
            test_dataset = test_dataset.select(
                range(data_args.max_predict_samples))
        with training_args.main_process_first(
                desc="prediction dataset map pre-processing"):
            test_dataset = test_dataset.map(
                lambda ex: {'label': label2id[ex['label']] if 'label' in ex
                            else 1})  # Always predict TRUE
            test_dataset = test_dataset.map(
                preprocess_function,
                batched=True,
                desc="Running tokenizer on prediction dataset",
            )
            columns_to_return = ['input_ids', 'label', 'attention_mask']
            test_dataset.set_format(type='torch', columns=columns_to_return)

        if data_args.max_predict_samples is not None:
            contra_dataset = contra_dataset.select(
                range(data_args.max_predict_samples))
        with training_args.main_process_first(
                desc="prediction dataset map pre-processing"):
            contra_dataset = contra_dataset.map(
                lambda ex: {'label': label2id[ex['label']]})
            contra_dataset = contra_dataset.map(
                preprocess_function,
                batched=True,
                desc="Running tokenizer on prediction dataset",
            )
            columns_to_return = ['input_ids', 'label', 'attention_mask']
            contra_dataset.set_format(type='torch', columns=columns_to_return)

    # Get the metric function
    metric = load_metric("accuracy")

    # You can define your custom compute_metrics function. It takes an `EvalPrediction` object (a namedtuple with a
    # predictions and label_ids field) and has to return a dictionary string to float.
    def compute_metrics(p: EvalPrediction):
        preds = p.predictions[0] if isinstance(p.predictions,
                                               tuple) else p.predictions
        preds = np.argmax(preds, axis=1)
        return metric.compute(predictions=preds, references=p.label_ids)

    # Initialize our Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset if training_args.do_train else None,
        eval_dataset=eval_dataset if training_args.do_eval else None,
        compute_metrics=compute_metrics,
        tokenizer=tokenizer,
        data_collator=default_data_collator,
    )

    # Training
    if training_args.do_train:
        checkpoint = None
        if training_args.resume_from_checkpoint is not None:
            checkpoint = training_args.resume_from_checkpoint
        elif last_checkpoint is not None:
            checkpoint = last_checkpoint
        train_result = trainer.train(resume_from_checkpoint=checkpoint)
        metrics = train_result.metrics
        max_train_samples = (
            data_args.max_train_samples if data_args.max_train_samples is not None else len(
                train_dataset)
        )
        metrics["train_samples"] = min(max_train_samples, len(train_dataset))

        trainer.save_model()  # Saves the tokenizer too for easy upload

        trainer.log_metrics("train", metrics)
        trainer.save_metrics("train", metrics)
        trainer.save_state()

    # Evaluation
    if training_args.do_eval:
        logger.info("*** Evaluate ***")
        metrics = trainer.evaluate(eval_dataset=eval_dataset)

        max_eval_samples = data_args.max_eval_samples if data_args.max_eval_samples is not None else len(
            eval_dataset)
        metrics["eval_samples"] = min(max_eval_samples, len(eval_dataset))

        trainer.log_metrics("eval", metrics)
        trainer.save_metrics("eval", metrics)

    # Test Set Prediction
    if training_args.do_predict:
        logger.info("*** Predict: Test ***")
        predictions, labels, metrics = trainer.predict(test_dataset)

        max_predict_samples = (
            data_args.max_predict_samples if data_args.max_predict_samples is not None else len(
                test_dataset)
        )
        metrics["predict_samples"] = min(max_predict_samples, len(test_dataset))

        trainer.log_metrics("predict", metrics)
        trainer.save_metrics("predict", metrics)

        predictions = np.argmax(predictions, axis=1)
        output_predict_file = os.path.join(training_args.output_dir,
                                           "test_predictions.txt")
        if trainer.is_world_process_zero():
            with open(output_predict_file, "w") as writer:
                writer.write("index\tprediction\n")
                for index, item in enumerate(predictions):
                    item = id2label[item]
                    writer.write(f"{index}\t{item}\n")

        logger.info("*** Predict: Contrast ***")
        predictions, labels, metrics = trainer.predict(contra_dataset)

        max_predict_samples = (
            data_args.max_predict_samples if data_args.max_predict_samples is not None else len(
                contra_dataset)
        )
        metrics["contra_samples"] = min(max_predict_samples,
                                        len(contra_dataset))

        trainer.log_metrics("contra", metrics)
        trainer.save_metrics("contra", metrics)

        predictions = np.argmax(predictions, axis=1)
        output_predict_file = os.path.join(training_args.output_dir,
                                           "contra_predictions.txt")
        if trainer.is_world_process_zero():
            with open(output_predict_file, "w") as writer:
                writer.write("index\tprediction\n")
                for index, item in enumerate(predictions):
                    item = id2label[item]
                    writer.write(f"{index}\t{item}\n")


if __name__ == '__main__':
    main()
