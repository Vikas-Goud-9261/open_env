from codebleu import calc_codebleu
from typing import Dict, Tuple
from functools import lru_cache

class CodeBLEU():

    def __init__(self, weights = (0.25,0.25,0.25,0.25)):
        self.weights = weights

    @staticmethod
    @lru_cache(maxsize=500)
    def _cached_score(code:str , reference_code:str, language:str, weights:Tuple) -> Dict:
        
        result = calc_codebleu(predictions= [code], references= [[reference_code]], lang = language, weights= weights)
        return result

    def score(self, code:str, reference_code:str, language:str) -> Dict:
        return self._cached_score(code, reference_code, language, self.weights)


if __name__ == '__main__':
    code = """def compute_factorial(x):
    value = 1
    counter = 1

    while counter <= x:
        value = value * counter
        counter += 1
    
    return value

    number = 5
    print(compute_factorial(number))"""

    reference_code = """def factorial(n):
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return result

    num = 5
    print(factorial(num))"""

    javascript_code = """
    function reverseStringCandidate(str) {
    let reversed = "";
    for (let i = str.length - 1; i >= 0; i--) {
        reversed += str[i];
    }
    return reversed;
    }
    """
    javascript_ref_code = """
    function reverseStringReference(str) {
        return str.split('').reverse().join('');
    }

    """
    cb = CodeBLEU()
    result = cb.score(code = code , reference_code = reference_code, language = 'python')
    print(result)
