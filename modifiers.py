"""
modifiers.py

This module defines the base Modifier class, as well as subclasses for injecting items 
(ItemInjection) and HTML tags (HTMLInjection) into text, as well as composing multiple 
modifiers (CompositeModifier).
"""

import random
import re

class Modifier:
    """
    Base class for applying modifications/corruptions to text-label pairs.

    Subclasses must implement the __call__ method to define specific transformations.
    
    Example:
        class MyModifier(Modifier):
            def __call__(self, text: str, label: Any) -> tuple[str, Any]:
                # custom transformation here
                return transformed_text, transformed_label
    """
    def __call__(self, text: str, label):
        """
        Apply the transformation to a single text-label pair.

        Args:
            text (str): The input text to transform.
            label: The associated label.
        
        Returns:
            tuple: (transformed_text, transformed_label)
        """
        raise NotImplementedError("Subclasses must implement __call__")

class CompositeModifier:
    """
    CompositeModifier chains multiple Modifier instances together.
    
    Each modifier from the list is applied sequentially to the text. This enables
    the combination of various transformations or injections into one composite operation.
    """
    def __init__(self, modifiers: list):
        """
        Initialize a CompositeModifier instance.
        
        Args:
            modifiers (list): A list of modifier instances (subclasses of Modifier) 
                              to be applied sequentially.
        """
        self.modifiers = modifiers

    def __call__(self, text: str, label):
        """
        Apply all modifiers in sequence to the given (text, label).

        Args:
            text (str): The input text.
            label: The associated label.

        Returns:
            tuple: The modified (text, label) pair after all transformations.
        """
        for modifier in self.modifiers:
            text, label = modifier(text, label)
        return text, label


class ItemInjection(Modifier):
    """
    A Modifier that injects items into text. 
    This class supports creation via three different approaches:
    - from_list: Using a predefined list of injection items.
    - from_file: Reading injection items from a file.
    - from_function: Using a custom function to generate injections.
    """
    def __init__(self, injection_source, location: str = "random", token_proportion: float = 0.1, seed=None):
        """
        Initialize an ItemInjection instance.

        Args:
            injection_source (callable): A function that returns an injection token.
            location (str): Where to inject the token ("beginning", "random", "end").
            token_proportion (float): Proportion of tokens in the text to be affected.
            seed (int, optional): Seed for reproducibility.
        """
        assert callable(injection_source), "injection_source must be callable"
        self.injection_source = injection_source
        self.location = location
        self.token_proportion = token_proportion
        self.rng = random.Random(seed)

        assert 0 <= token_proportion <= 1, "token_proportion must be between 0 and 1"
        assert location in {"beginning", "random", "end"}, "location must be 'beginning', 'random', or 'end'"

    def __call__(self, text: str, label):
        """
        Inject tokens into the text at specified locations.

        Args:
            text (str): The input text to modify.
            label: The original label (unchanged).

        Returns:
            tuple: The modified text and the original label.
        """
        words = text.split()
        num_tokens = len(words)

        # Ensure at least one token is injected
        num_to_inject = max(1, int(num_tokens * self.token_proportion))

        injections = [self.injection_source() for _ in range(num_to_inject)]

        if self.location == "beginning":
            words = injections + words
        elif self.location == "end":
            words = words + injections
        elif self.location == "random":
            for injection in injections:
                pos = self.rng.randint(0, len(words))
                words.insert(pos, injection)

        return " ".join(words), label  # return modified text and unchanged label

    @classmethod
    def from_list(cls, items: list, location: str = "random", token_proportion: float = 0.1, seed=None):
        """
        Create an ItemInjection instance using a predefined list of tokens.

        Args:
            items (list): List of token strings to choose from.
            location (str): Where to inject tokens ("beginning", "random", "end").
            token_proportion (float): Proportion of text tokens to be affected.
            seed (int, optional): Seed for reproducibility.

        Returns:
            ItemInjection: Configured instance.
        """
        rng = random.Random(seed)
        def injection_source():
            return rng.choice(items)
        return cls(injection_source, location=location, token_proportion=token_proportion, seed=seed)

    @classmethod
    def from_file(cls, file_path: str, location: str = "random", token_proportion: float = 0.1, seed=None):
        """
        Create an ItemInjection instance using tokens read from a file.

        Each non-empty line becomes a potential injection item.

        Args:
            file_path (str): Path to the file with one token per line.
            location (str): Where to inject tokens.
            token_proportion (float): Proportion of tokens to inject.
            seed (int, optional): Seed for reproducibility.

        Returns:
            ItemInjection: Configured instance.
        """
        with open(file_path, "r", encoding="utf-8") as file:
            items = [line.strip() for line in file if line.strip()]
        return cls.from_list(items, location=location, token_proportion=token_proportion, seed=seed)

    @classmethod
    def from_function(cls, injection_func, location: str = "random", token_proportion: float = 0.1, seed=None):
        """
        Create an ItemInjection instance using a custom function to generate injections.

        Args:
            injection_func (callable): Function that returns a new injection token each time.
            location (str): Where to inject tokens.
            token_proportion (float): Proportion of text to inject into.
            seed (int, optional): Seed for reproducibility (used only for insertion position).

        Returns:
            ItemInjection: Configured instance.
        """
        assert callable(injection_func), "injection_func must be callable"
        return cls(injection_func, location=location, token_proportion=token_proportion, seed=seed)
    

class HTMLInjection(Modifier):
    """
    A Modifier that injects HTML tags into a text.
    
    This injection picks a random tag from a file or list. Some items in the file/list
    have both opening and closing tags, while others only have a single tag.
    
    Injection behavior:
      - For "beginning": Inserts the opening tag at the beginning of the target text
        and, if available, inserts the closing tag at a random position.
      - For "random": Inserts the opening tag at a random position and, if available, inserts the
        closing tag at a random position after the opening tag.
      - For "end": Inserts the opening tag at a random position and, if available, appends the closing tag
        at the end of the target. If no closing tag is available, only the opening tag is inserted at the end.
      
    The optional parameter "level" allows the injection to be applied only inside the L-th nested
    HTML tag. For example:
        - If level=0, the injection is applied at the outermost level.
        - If level=2, and the text is "<a>asdf <b> asdf sadf asdf </b> asdf asdf </a>", then the injection
          is performed only within the inner <b>...</b> region.
    """

    def __init__(self, file_path: str, location: str = "random", level: int = None, seed=None):
        """
        Initialize an HTMLInjection instance.

        Args:
            file_path (str): Path to the file containing HTML tag definitions.
            location (str): Where to inject ("beginning", "random", or "end").
            level (int): The nested HTML level at which to perform the injection.
            seed (int, optional): Seed for deterministic random behavior.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            self.tags = [line.strip() for line in f if line.strip()]
        self.location = location
        self.level = level
        self.rng = random.Random(seed)

    @classmethod
    def from_file(cls, file_path: str, location: str = "random", level: int = None, seed=None):
        """
        Create an HTMLInjection instance from a file.

        Args:
            file_path (str): Path to the file containing tag definitions.
            location (str): Injection location.
            level (int): Nesting level.
            seed (int, optional): Random seed.

        Returns:
            HTMLInjection: The configured instance.
        """
        return cls(file_path, location=location, level=level, seed=seed)

    @classmethod
    def from_list(cls, tags: list, location: str = "random", level: int = None, seed=None):
        """
        Create an HTMLInjection instance using a predefined list of tag definitions.

        Args:
            tags (list): List of tag strings (either single or opening/closing pairs).
            location (str): Injection location.
            level (int): Nesting level.
            seed (int, optional): Random seed.

        Returns:
            HTMLInjection: The configured instance.
        """
        instance = cls.__new__(cls)
        instance.tags = tags
        instance.location = location
        instance.level = level
        instance.rng = random.Random(seed)
        return instance

    def _choose_tag(self):
        """
        Randomly choose a tag from the loaded list.

        Returns:
            tuple: (opening_tag, closing_tag or None)
        """
        line = self.rng.choice(self.tags)
        parts = line.split()
        if len(parts) >= 2:
            return parts[0], parts[1]
        else:
            return parts[0], None

    def _inject_into_tokens(self, tokens, opening, closing, location):
        """
        Injects opening and closing tags into a token list based on location.

        Args:
            tokens (list): List of token strings.
            opening (str): Opening tag.
            closing (str or None): Closing tag.
            location (str): Where to inject.

        Returns:
            list: Modified token list.
        """
        if location == "beginning":
            new_tokens = [opening] + tokens[:]
            if closing:
                pos = self.rng.randint(1, len(new_tokens))
                new_tokens.insert(pos, closing)
            return new_tokens
        elif location == "end":
            new_tokens = tokens[:]
            if closing:
                pos = self.rng.randint(0, len(new_tokens))
                new_tokens.insert(pos, opening)
                new_tokens.append(closing)
            else:
                new_tokens.append(opening)
            return new_tokens
        elif location == "random":
            new_tokens = tokens[:]
            pos_open = self.rng.randint(0, len(new_tokens))
            new_tokens.insert(pos_open, opening)
            if closing:
                pos_close = self.rng.randint(pos_open + 1, len(new_tokens))
                new_tokens.insert(pos_close, closing)
            return new_tokens
        else:
            return tokens

    def _inject(self, text, location):
        """
        Injects HTML tags into the full text.

        Args:
            text (str): Input text.
            location (str): Injection location.

        Returns:
            str: Modified text.
        """
        tokens = text.split()
        opening, closing = self._choose_tag()
        new_tokens = self._inject_into_tokens(tokens, opening, closing, location)
        return " ".join(new_tokens)

    def _find_level_span(self, text, level):
        """
        Find the first span inside the desired HTML nesting level.

        Args:
            text (str): Input HTML text.
            level (int): Desired nesting level.

        Returns:
            tuple or None: (start, end) of the content region, or None if not found.
        """
        tag_regex = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)[^>]*>")
        stack = []
        for match in tag_regex.finditer(text):
            tag_str = match.group(0)
            tag_name = match.group(1)
            if not tag_str.startswith("</"):
                stack.append((tag_name, match.end()))
            else:
                if stack:
                    open_tag, start_index = stack.pop()
                    if len(stack) == level - 1:
                        return (start_index, match.start())
        return None

    def __call__(self, text: str, label):
        """
        Inject HTML tags into the given text.

        Args:
            text (str): Input text.
            label: Associated label.

        Returns:
            tuple: Modified text and original label.
        """
        if self.level is None:
            return self._inject(text, self.location), label
        elif self.level == 0:
            opening, closing = self._choose_tag()
            if closing:
                return f"{opening}{text}{closing}", label
            else:
                return f"{opening}{text}{opening}", label
        else:
            span = self._find_level_span(text, self.level)
            if span is None:
                return self._inject(text, self.location), label
            start, end = span
            target = text[start:end]
            injected = self._inject(target, self.location)
            return text[:start] + injected + text[end:], label