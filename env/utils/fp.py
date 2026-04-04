from __future__ import annotations
from tree_sitter import Language, Parser
import tree_sitter_python, tree_sitter_javascript
from typing import List, Dict
from functools import lru_cache
from pathlib import Path

class ASTParser:

    LANG_PATHS = {
        'python' : 'ast_grammar/tree-sitter-python/python.so',
        'cpp' : 'ast_grammar/tree-sitter-cpp/cpp.so',
        'c' : 'ast_grammar/tree-sitter-c/c.so',
        'java' : 'ast_grammar/tree-sitter-java/java.so',
        'javascript' : 'ast_grammar/tree-sitter-javascript/javascript.so'
    }

    LANG_POINTS = {
        'python' : tree_sitter_python,
        'javascript' : tree_sitter_javascript
    }
    def __init__(self):
        self._parsers: Dict[str ,Parser] = {}

    @lru_cache(maxsize=None)
    def _load_language(self, language:str)-> Language:
        #grammar_path = self.LANG_PATHS[language]
        lang_sel = self.LANG_POINTS[language]
        #if not Path(grammar_path).exists():
            #raise FileNotFoundError(f'Grammar not built at path : {grammar_path}')
        #return Language.load(grammar_path) 
        print(lang_sel)
        if language not in self.LANG_POINTS:
            raise ValueError(f"Unsupported language : {language}") 
        return Language(lang_sel.language())

    def build_parser_for_language(self, language:str) -> Parser:
        if language not in self._parsers:
            lang_grammar = self._load_language(language)
            parser = Parser(lang_grammar)
            self._parsers[language] = parser
        return self._parsers[language]

    def parse(self, code: str, language:str ):
        parser = self.build_parser_for_language(language)
        tree = parser.parse(code.encode('utf-8'))
        return tree
if __name__ == "__main__":
    candidate_code = """
    def compute_factorial(x):
    value = 1
    counter = 1

    while counter <= x:
        value = value * counter
        counter += 1
    
    return value

    number += 1
    print(compute_factorial(number))"""

    candidate_code_c = """
    #include <bits/stdc++.h>
    using namespace std;

    int main() {
        int n;
        cin >> n;

        int total = 0;
        int i = 1;
        while (i <= n) {
            total = total + i;
            i++;
        }

        cout << total;
        return 0;
    }

    """
    reference_code = """def factorial(n):
        if n == 0 or n == 1:
            return 1
        
        result = 1
        for i in range(2, n + 1):
            result *= i
        
        return result

        num = 5
        print(factorial(num))"""

    reference_code_c = """
    #include <iostream>
    using namespace std;

    int main() {
        int n;
        cin >> n;

        int sum = 0;
        for (int i = 1; i <= n; i++) {
            sum += i;
        }

        cout << sum << endl;
        return 0;
    }

    """
    ast = ASTParser()
    cand_tree = ast.parse(candidate_code, 'python')
    print(cand_tree.root_node)


