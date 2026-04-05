import difflib
from codebleu import calc_codebleu
from typing import Dict, Tuple
from functools import lru_cache


SUPPORTED_LANGUAGES = ['python', 'java', 'javascript', 'cpp', 'c']


class CodeBLEU():

    def __init__(self, weights: Tuple = (0.25, 0.25, 0.25, 0.25)):
        self.weights = weights

    @staticmethod
    @lru_cache(maxsize=500)
    def _cached_score(
        code          : str,
        reference_code: str,
        language      : str,
        weights       : Tuple
    ) -> Dict:
        try:
            result = calc_codebleu(
                predictions = [code],
                references  = [[reference_code]],
                lang        = language,
                weights     = weights
            )
            return result

        except Exception:
            # Fallback to difflib if codebleu fails
            similarity = difflib.SequenceMatcher(
                None,
                code.strip(),
                reference_code.strip()
            ).ratio()
            return {'codebleu': similarity}

    def score(
        self,
        code          : str,
        reference_code: str,
        language      : str
    ) -> Dict:
        # Fallback if unsupported language
        if language not in SUPPORTED_LANGUAGES:
            similarity = difflib.SequenceMatcher(
                None,
                code.strip(),
                reference_code.strip()
            ).ratio()
            return {'codebleu': similarity}

        return self._cached_score(
            code,
            reference_code,
            language,
            self.weights
        )


if __name__ == '__main__':
    code = """\
def compute_factorial(x):
    value = 1
    counter = 1
    while counter <= x:
        value = value * counter
        counter += 1
    return value
"""

    reference_code = """\
def factorial(n):
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
"""

    cb = CodeBLEU()
    result = cb.score(
        code           = code,
        reference_code = reference_code,
        language       = 'python'
    )
    print(result)