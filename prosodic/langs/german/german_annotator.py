from ...imports import *
from .german_functions import (
    is_vowel, 
    is_consonant, 
    is_diphthong, 
    is_heavy_syllable,
    is_schwa,
    split_syllable as german_split_syllable
)

class Syllable:
    """
    Represents a syllable with onset, nucleus, and coda components.
    """
    def __init__(self, text, stress=0):
        self.text = text
        self.stress = stress
        onset, nucleus, coda = split_syllable(text)
        self.onset = onset
        self.nucleus = nucleus
        self.coda = coda
    
    def __str__(self):
        return self.text
    
    def __repr__(self):
        return f"Syllable('{self.text}', stress={self.stress})"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.text == other
        elif isinstance(other, Syllable):
            return self.text == other.text
        return False

class Annotation:
    def __init__(self, token, orth_token=None):
        """Initialize a German annotation object.
        
        Args:
            token (str): The token to annotate
            orth_token (str, optional): The orthographic version of the token
        """
        self.token = token.lower()  # Normalize to lowercase
        self.orth_token = orth_token if orth_token else token
        self.has_repetition = False
        self.syllables = []
        self.stresses = []
        self.split_sylls = []
        self._process_token()
    
    def _remove_repetition(self, token):
        """
        Remove repetition from a token by detecting repeating patterns.
        
        Args:
            token (str): The token to process
            
        Returns:
            tuple: (processed_token, has_repetition)
        """
        if not token or len(token) < 2:
            return token, False
            
        # Check for repetitive patterns
        token_len = len(token)
        has_repetition = False
        
        # Try pattern lengths from 1 to half the token length
        for pattern_len in range(1, token_len // 2 + 1):
            # Get all possible patterns of this length
            for start in range(pattern_len):
                if start + pattern_len > token_len:
                    continue
                    
                pattern = token[start:start+pattern_len]
                if not pattern:
                    continue
                
                # Check if this pattern repeats consecutively
                repeat_count = 1
                pos = start + pattern_len
                
                while pos + pattern_len <= token_len and token[pos:pos+pattern_len] == pattern:
                    repeat_count += 1
                    pos += pattern_len
                
                # If we found at least one repeat
                if repeat_count > 1:
                    # If the pattern covers the entire string
                    if start == 0 and pos >= token_len:
                        has_repetition = True
                        return pattern, has_repetition
                    
                    # If the pattern covers a significant portion (≥ 60%)
                    covered_len = repeat_count * pattern_len
                    if covered_len >= token_len * 0.6:
                        has_repetition = True
                        # Return just the pattern that's repeating
                        return pattern, has_repetition
        
        return token, has_repetition
    
    def _process_token(self):
        """Process a token into syllables and stresses."""
        # First check for repetitions
        processed_token, self.has_repetition = self._remove_repetition(self.token)
        
        # If we found repetition, use the processed token
        token_to_process = processed_token if self.has_repetition else self.token
        
        # Syllabify the token
        self.syllables = syllabify(token_to_process)
        
        # Get stresses
        self.stresses = get_stresses(token_to_process, self.syllables)
        
        # Split syllables into onset, nucleus, coda
        self.split_sylls = []
        for syll in self.syllables:
            onset, nucleus, coda = split_syllable(syll)
            self.split_sylls.append([onset, nucleus, coda])
    
    @property
    def sylls(self):
        """Get the syllables."""
        return self.syllables
    
    @property
    def stress(self):
        """Get the stress pattern."""
        return self.stresses


def make_annotation(token, orth_token=None):
    """
    Create a German annotation for a token.
    
    Args:
        token (str): The token to annotate
        orth_token (str, optional): The orthographic version of the token
        
    Returns:
        Annotation: An annotation object
    """
    return Annotation(token, orth_token)


def syllabify(token):
    """
    Syllabify a token using German syllabification rules.
    
    Args:
        token (str): The token to syllabify
        
    Returns:
        list: The syllables as strings
    """
    token = token.lower().strip()
    
    # Handle empty or very short tokens
    if not token:
        return []
    if len(token) <= 1:
        return [token]
    
    # Define vowels and consonant groups
    vowels = 'aeiouäöüy'
    diphthongs = ['au', 'ei', 'ai', 'eu', 'äu', 'ie']
    
    # Inseparable consonant clusters
    onset_clusters = {
        'pr', 'br', 'tr', 'dr', 'kr', 'gr', 'fr', 'vr',  # consonant + r
        'pl', 'bl', 'kl', 'gl', 'fl', 'vl',              # consonant + l
        'kn', 'gn', 'pf', 'ts', 'sch', 'st', 'sp',       # other common clusters
        'qu', 'ch', 'ck'                                  # special cases
    }
    
    # Find all vowel positions
    vowel_positions = []
    i = 0
    while i < len(token):
        # Check for diphthongs first
        if i < len(token) - 1 and token[i:i+2] in diphthongs:
            vowel_positions.append((i, i+2))  # Store start and end of diphthong
            i += 2
        elif token[i] in vowels:
            vowel_positions.append((i, i+1))  # Store start and end of vowel
            i += 1
        else:
            i += 1
    
    # If no vowels found, return the whole token
    if not vowel_positions:
        return [token]
    
    # Build syllables
    syllables = []
    start_idx = 0
    
    for i in range(len(vowel_positions)):
        vowel_start, vowel_end = vowel_positions[i]
        
        # If this is the last vowel or there are no consonants between this vowel and the next
        if i == len(vowel_positions) - 1 or vowel_end == vowel_positions[i+1][0]:
            # Add remaining portion of token to syllables
            syllables.append(token[start_idx:])
            break
        
        # Get consonants between this vowel and the next
        next_vowel_start = vowel_positions[i+1][0]
        consonants = token[vowel_end:next_vowel_start]
        
        # Apply consonant cluster rules
        if not consonants:
            # No consonants between vowels
            syllables.append(token[start_idx:vowel_end])
            start_idx = vowel_end
        elif len(consonants) == 1:
            # Single consonant goes with the next syllable (maximize onset)
            syllables.append(token[start_idx:vowel_end])
            start_idx = vowel_end
        else:
            # Multiple consonants - need to apply syllabification rules
            split_point = 0
            
            # Check if the consonant cluster is an inseparable onset
            if consonants in onset_clusters:
                # The whole cluster goes to the next syllable
                syllables.append(token[start_idx:vowel_end])
                start_idx = vowel_end
            elif len(consonants) >= 2 and consonants[-2:] in onset_clusters:
                # The last two consonants form an onset cluster for the next syllable
                split_point = len(consonants) - 2
                syllables.append(token[start_idx:vowel_end + split_point])
                start_idx = vowel_end + split_point
            else:
                # Default rule: Leave one consonant for the next syllable
                split_point = len(consonants) - 1
                syllables.append(token[start_idx:vowel_end + split_point])
                start_idx = vowel_end + split_point
    
    # Add final part if needed
    if start_idx < len(token):
        syllables.append(token[start_idx:])
    
    # Check for repetitive patterns
    if len(syllables) >= 4:
        for pattern_len in range(1, len(syllables) // 2 + 1):
            if len(syllables) % pattern_len == 0:
                is_repetitive = True
                pattern = syllables[:pattern_len]
                
                for j in range(pattern_len, len(syllables), pattern_len):
                    if syllables[j:j+pattern_len] != pattern:
                        is_repetitive = False
                        break
                
                if is_repetitive:
                    return syllables[:pattern_len]
    
    return syllables


def get_stresses(token, syllables=None):
    """
    Determine the stress pattern for a list of German syllables.
    
    Args:
        token (str): The word to analyze
        syllables (list, optional): Pre-computed syllables
        
    Returns:
        list: The stress pattern as a list of 0s and 1s
    """
    if not token:
        return [[]]
    
    if syllables is None:
        syllables = syllabify(token)
    
    if not syllables:
        return [[]]
        
    num_syllables = len(syllables)
    
    # Default: Stress falls on first syllable in German
    stress = [0] * num_syllables
    stress[0] = 1
    
    # Check for common unstressed prefixes
    prefixes = {'ge', 'be', 'ver', 'zer', 'ent', 'er', 'emp', 'miss'}
    if num_syllables > 1 and syllables[0] in prefixes:
        stress[0] = 0
        stress[1] = 1
    
    # Check for loanwords with final stress (more complex rules would be needed for accurate prediction)
    loanword_suffixes = {'tion', 'tät', 'ment', 'ant', 'ent', 'är', 'al', 'iv'}
    if num_syllables > 1:
        last_syllable = syllables[-1]
        if any(last_syllable.endswith(suffix) for suffix in loanword_suffixes):
            stress = [0] * num_syllables
            stress[-1] = 1
    
    # Apply secondary stress for longer words
    if num_syllables >= 3:
        # Place secondary stress on alternating syllables
        primary_pos = stress.index(1)
        for i in range(num_syllables):
            if i != primary_pos and abs(i - primary_pos) % 2 == 0:
                stress[i] = 2
    
    return [stress]


def get_sylls_ll_rule(token, orth_token=None):
    """
    Get syllables and stress pattern for a token with handling for repetitions.
    
    Args:
        token (str): The token to annotate
        orth_token (str, optional): The orthographic version of the token
        
    Returns:
        tuple: (syllables_text, syllables_ipa, stresses, dict_sylls)
    """
    # Create annotation
    annotation = make_annotation(token, orth_token)
    
    # Extract syllables and stress patterns
    sylls_text = annotation.sylls
    
    # Convert stress format from list to string
    if isinstance(annotation.stress, list) and annotation.stress:
        stresses = ''.join(map(str, annotation.stress[0]))
    else:
        stresses = annotation.stress
    
    # Create the correct return format
    sylls_ipa_ll = [[syll] for syll in sylls_text]
    dict_sylls = {}  # Empty dict as we're not using a pronunciation dictionary
    
    return sylls_text, sylls_ipa_ll, stresses, dict_sylls


def get_sylls_ll(token, orth=None):
    """
    Get syllables and stress pattern with a default lightweight format.
    
    Args:
        token (str): The token to analyze
        orth (str, optional): Orthographic form of the token
        
    Returns:
        tuple: (syllables_text, syllables_ipa, stresses, dict_sylls)
    """
    return get_sylls_ll_rule(token, orth)


def split_syllable(syllable):
    """
    Split a syllable into onset, nucleus, and coda.
    
    Args:
        syllable (str): The syllable to split
        
    Returns:
        tuple: (onset, nucleus, coda)
    """
    return german_split_syllable(syllable) 