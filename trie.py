#!/usr/bin/env python3
"""trie — Prefix tree for fast string lookup and autocomplete. Zero deps."""
import sys

class TrieNode:
    __slots__ = ('children', 'is_end', 'value', 'count')
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.value = None
        self.count = 0

class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.size = 0

    def insert(self, key, value=True):
        node = self.root
        for ch in key:
            node.count += 1
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.count += 1
        if not node.is_end:
            self.size += 1
        node.is_end = True
        node.value = value

    def search(self, key):
        node = self._find(key)
        return node.value if node and node.is_end else None

    def starts_with(self, prefix):
        node = self._find(prefix)
        if not node:
            return []
        results = []
        self._collect(node, list(prefix), results)
        return results

    def _find(self, key):
        node = self.root
        for ch in key:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

    def _collect(self, node, path, results, limit=20):
        if len(results) >= limit:
            return
        if node.is_end:
            results.append(''.join(path))
        for ch in sorted(node.children):
            path.append(ch)
            self._collect(node.children[ch], path, results, limit)
            path.pop()

    def delete(self, key):
        def _del(node, key, depth):
            if depth == len(key):
                if not node.is_end:
                    return False
                node.is_end = False
                node.count -= 1
                self.size -= 1
                return len(node.children) == 0
            ch = key[depth]
            if ch not in node.children:
                return False
            should_delete = _del(node.children[ch], key, depth + 1)
            if should_delete:
                del node.children[ch]
            node.count -= 1
            return not node.is_end and len(node.children) == 0
        _del(self.root, key, 0)

def main():
    t = Trie()
    words = ["apple", "app", "application", "apply", "apt", "banana", "band", "ban"]
    for w in words:
        t.insert(w)
    print(f"Trie ({t.size} words):")
    for prefix in ["app", "ban", "z"]:
        matches = t.starts_with(prefix)
        print(f'  "{prefix}" -> {matches}')
    print(f'\n  search("apple"): {t.search("apple")}')
    print(f'  search("ap"): {t.search("ap")}')
    t.delete("app")
    print(f'  After delete("app"), starts_with("app"): {t.starts_with("app")}')

if __name__ == "__main__":
    main()
