# Copyright (c) Alibaba, Inc. and its affiliates.

from typing import Dict, Iterable, List

from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge

from modelscope.metainfo import Metrics
from modelscope.metrics.base import Metric
from modelscope.metrics.builder import METRICS, MetricKeys
from modelscope.utils.registry import default_group


@METRICS.register_module(
    group_key=default_group, module_name=Metrics.text_gen_metric)
class TextGenerationMetric(Metric):
    """The metric computation class for text generation classes.

    This metric class calculates F1 of the rouge scores for the whole evaluation dataset.
    """

    def __init__(self):
        self.preds: List[str] = []
        self.tgts: List[str] = []
        self.rouge = Rouge()

    @staticmethod
    def is_chinese_char(char: str):
        # the length of char must be 1
        return '\u4e00' <= char <= '\u9fa5'

    # add space for each chinese char
    def rebuild_str(self, string: str):
        return ' '.join(''.join([
            f' {char} ' if self.is_chinese_char(char) else char
            for char in string
        ]).split())

    def add(self, outputs: Dict[str, List[str]], inputs: Dict = None):
        ground_truths = outputs['tgts']
        eval_results = outputs['preds']
        for truth in ground_truths:
            self.tgts.append(self.rebuild_str(truth))
        for result in eval_results:
            self.preds.append(self.rebuild_str(result))

    def evaluate(self):

        def mean(iter: Iterable) -> float:
            return sum(iter) / len(self.preds)

        rouge_scores = self.rouge.get_scores(hyps=self.preds, refs=self.tgts)
        rouge_1 = mean(map(lambda score: score['rouge-1']['f'], rouge_scores))
        rouge_l = mean(map(lambda score: score['rouge-l']['f'], rouge_scores))
        pred_split = tuple(pred.split(' ') for pred in self.preds)
        tgt_split = tuple(tgt.split(' ') for tgt in self.tgts)
        bleu_1 = mean(
            sentence_bleu([tgt], pred, weights=(1, 0, 0, 0))
            for pred, tgt in zip(pred_split, tgt_split))
        bleu_4 = mean(
            sentence_bleu([tgt], pred)
            for pred, tgt in zip(pred_split, tgt_split))
        return {
            MetricKeys.ROUGE_1: rouge_1,
            MetricKeys.ROUGE_L: rouge_l,
            MetricKeys.BLEU_1: bleu_1,
            MetricKeys.BLEU_4: bleu_4
        }
