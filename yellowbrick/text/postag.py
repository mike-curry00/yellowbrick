# yellowbrick.text.postag
# Implementation of part-of-speech visualization for text.
#
# Author:   Rebecca Bilbro
# Created:  2019-02-18 13:12
#
# Copyright (C) 2019 The scikit-yb developers
# For license information, see LICENSE.txt
#
# ID: postag.py bilbro@gmail.com $

"""
Implementation of part-of-speech visualization for text,
enabling the user to visualize a single document or
small subset of documents.
"""

##########################################################################
# Imports
##########################################################################

import numpy as np

from yellowbrick.draw import bar_stack
from yellowbrick.text.base import TextVisualizer
from yellowbrick.style.colors import resolve_colors
from yellowbrick.exceptions import YellowbrickValueError

##########################################################################
# Part-of-speech tag punctuation and labels
##########################################################################

# NOTE: Penn Treebank converts all sentence closers (!,?,;) to periods
PUNCT_TAGS = [".", ":", ",", "``", "''", "(", ")", "#", "$"]

TAGSET_NAMES = {
    "penn_treebank": "Penn Treebank",
    "universal": "Universal Dependencies"
}

PENN_TAGS = [
    "noun", "verb", "adjective", "adverb", "preposition", "determiner",
    "pronoun", "conjunction", "infinitive", "wh- word", "modal", 
    "possessive", "existential", "punctuation", "digit", "non-English",
    "interjection", "list", "symbol", "other"
]

UNIVERSAL_TAGS = [
    "noun", "verb", "adjective", "adverb", "adposition", "determiner",
    "pronoun", "conjunction", "infinitive", "punctuation", "number", 
    "interjection", "symbol", "other"
]


##########################################################################
# PosTagVisualizer
##########################################################################

class PosTagVisualizer(TextVisualizer):
    """
    Parts of speech (e.g. verbs, nouns, prepositions, adjectives)
    indicate how a word is functioning within the context of a sentence.
    In English as in many other languages, a single word can function in
    multiple ways. Part-of-speech tagging lets us encode information not
    only about a word’s definition, but also its use in context (for
    example the words “ship” and “shop” can be either a verb or a noun,
    depending on the context).
    
    The PosTagVisualizer creates a bar chart to visualize the relative
    proportions of different parts-of-speech in a corpus.
    
    Note that the PosTagVisualizer requires documents to already be
    part-of-speech tagged; the visualizer expects the corpus to come in
    the form of a list of (document) lists of (sentence) lists of
    (tag, token) tuples.
    
    Parameters
    ----------
    ax : matplotlib axes
        The axes to plot the figure on. 

    tagset: string
        The tagset that was used to perform part-of-speech tagging.
        Either "penn_treebank" or "universal", defaults to "penn_treebank".
        Use "universal" if corpus has been tagged using SpaCy.

    colors : list or tuple of strings
        Specify the colors for each individual part-of-speech. Will override
        colormap if both are provided.

    colormap : string or matplotlib cmap
        Specify a colormap to color the parts-of-speech.

    frequency: bool {True, False}, default: False
        If set to True, part-of-speech tags will be plotted according to frequency,
        from most to least frequent.

    stack : bool {True, False}, default : False
        Plot the PosTag frequency chart as a per-class stacked bar chart. 
        Note that fit() requires y for this visualization.

    kwargs : dict
        Pass any additional keyword arguments to the PosTagVisualizer.
    
    Attributes
    ----------
    pos_tag_counts_: dict
        Mapping of part-of-speech tags to counts.
   
    Examples
    --------
    >>> viz = PosTagVisualizer()
    >>> viz.fit(X)
    >>> viz.poof()
    """

    def __init__(
        self,
        ax=None,
        tagset="penn_treebank",
        colormap=None,
        colors=None,
        frequency=False,
        stack=False,
        **kwargs
    ):
        super(PosTagVisualizer, self).__init__(ax=ax, **kwargs)

        self.tagset_names = TAGSET_NAMES

        if tagset not in self.tagset_names:
            raise YellowbrickValueError((
                "'{}' is an invalid tagset. Please choose one of {}."
            ).format(
                tagset, ", ".join(self.tagset_names.keys())
            ))
        else:
            self.tagset = tagset

        self.punct_tags = frozenset(PUNCT_TAGS)
        self.frequency = frequency
        self.colormap = colormap
        self.colors = colors
        self.stack = stack

    def fit(self, X, y=None, **kwargs):
        """
        Fits the corpus to the appropriate tag map.
        Text documents must be tokenized & tagged before passing to fit.
        
        Parameters
        ----------
        X : list or generator
            Should be provided as a list of documents or a generator
            that yields a list of documents that contain a list of
            sentences that contain (token, tag) tuples.

        y : ndarray or Series of length n
            An optional array of target values that are ignored by the
            visualizer.

        kwargs : dict
            Pass generic arguments to the drawing method
 
        Returns
        -------
        self : instance
            Returns the instance of the transformer/visualizer
        """
        self.labels_ = ['documents']
        if self.stack:
            if y is None:
                raise YellowbrickValueError("Specify y for stack=True")
            self.labels_ = np.unique(y)

        if self.tagset == "penn_treebank":
            self.pos_tag_counts_ = self._penn_tag_map()
            self._handle_treebank(X, y)

        elif self.tagset == "universal":
            self.pos_tag_counts_ = self._uni_tag_map()
            self._handle_universal(X, y)

        self.draw()

        return self

    def _penn_tag_map(self):
        """
        Returns a Penn Treebank part-of-speech tag map.
        """
        self._pos_tags = PENN_TAGS
        return self._make_tag_map(PENN_TAGS)

    def _uni_tag_map(self):
        """
        Returns a Universal Dependencies part-of-speech tag map.
        """
        self._pos_tags = UNIVERSAL_TAGS
        return self._make_tag_map(UNIVERSAL_TAGS)

    def _make_tag_map(self, tagset):
        """
        Returns a map of the tagset to a counter unless stack=True then returns
        a map of labels to a map of tagset to counters. 
        """
        # ensures the dict contains a zero counter per tag
        zeros = [0] * len(tagset)
        return {
            label: dict(zip(tagset, zeros))
            for label in self.labels_
        }
        return dict(zip(tagset, zeros))

    def _handle_universal(self, X, y=None):
        """
        Scan through the corpus to compute counts of each Universal
        Dependencies part-of-speech.

        Parameters
        ----------
        X : list or generator
            Should be provided as a list of documents or a generator
            that yields a list of documents that contain a list of
            sentences that contain (token, tag) tuples.
        """
        jump = {
            # combine proper and regular nouns
            "NOUN": "noun", "PROPN": "noun",
            "ADJ": "adjective",
            "VERB": "verb",
            # include particles with adverbs
            "ADV": "adverb", "PART": "adverb",
            "ADP": "adposition",
            "PRON": "pronoun",
            "CCONJ": "conjunction",
            "PUNCT": "punctuation",
            "DET": "determiner",
            "NUM": "number",
            "INTJ": "interjection",
            "SYM": "symbol",
        }

        for idx, tagged_doc in enumerate(X):
            for tagged_sent in tagged_doc:
                for _, tag in tagged_sent:
                    if tag == "SPACE":
                        continue
                    if self.stack:
                        counter = self.pos_tag_counts_[y[idx]] 
                    else:
                        counter = self.pos_tag_counts_['documents']

                    counter[jump.get(tag, "other")] += 1

    def _handle_treebank(self, X, y=None):
        """
        Create a part-of-speech tag mapping using the Penn Treebank tags

        Parameters
        ----------
        X : list or generator
            Should be provided as a list of documents or a generator
            that yields a list of documents that contain a list of
            sentences that contain (token, tag) tuples.
        """
        for idx, tagged_doc in enumerate(X):
            for tagged_sent in tagged_doc:
                for _, tag in tagged_sent:
                    if self.stack:
                        counter = self.pos_tag_counts_[y[idx]] 
                    else:
                        counter = self.pos_tag_counts_['documents']

                    if tag.startswith("N"):
                        counter["noun"] += 1
                    elif tag.startswith("J"):
                        counter["adjective"] += 1
                    elif tag.startswith("V"):
                        counter["verb"] += 1
                    # include particles with adverbs
                    elif tag.startswith("RB") or tag == "RP":
                        counter["adverb"] += 1
                    elif tag.startswith("PR"):
                        counter["pronoun"] += 1
                    elif tag.startswith("W"):
                        counter["wh- word"] += 1
                    elif tag == "CC":
                        counter["conjunction"] += 1
                    elif tag == "CD":
                        counter["digit"] += 1
                    # combine predeterminer and determiner
                    elif tag in ["DT" or "PDT"]:
                        counter["determiner"] += 1
                    elif tag == "EX":
                        counter["existential"] += 1
                    elif tag == "FW":
                        counter["non-English"] += 1
                    elif tag == "IN":
                        counter["preposition"] += 1
                    elif tag == "POS":
                        counter["possessive"] += 1
                    elif tag == "LS":
                        counter["list"] += 1
                    elif tag == "MD":
                        counter["modal"] += 1
                    elif tag in self.punct_tags:
                        counter["punctuation"] += 1
                    elif tag == "TO":
                        counter["infinitive"] += 1
                    elif tag == "UH":
                        counter["interjection"] += 1
                    elif tag == "SYM":
                        counter["symbol"] += 1
                    else:
                        counter["other"] += 1

    def draw(self, **kwargs):
        """
        Called from the fit method, this method creates the canvas and
        draws the part-of-speech tag mapping as a bar chart.

        Parameters
        ----------
        kwargs: dict
            generic keyword arguments.

        Returns
        -------
        ax : matplotlib axes
            Axes on which the PosTagVisualizer was drawn.
        """
        # Converts nested dict to nested list
        pos_tag_counts = np.array([
            list(i.values()) for i in self.pos_tag_counts_.values()
        ])
        # stores sum of nested list column wise
        pos_tag_sum = np.sum(pos_tag_counts, axis=0)

        if self.frequency:
            # sorts the count and tags by sum for frequency true
            idx = (pos_tag_sum).argsort()[::-1]
            self._pos_tags = np.array(self._pos_tags)[idx] 
            pos_tag_counts = pos_tag_counts[:,idx]

        if self.stack:
            bar_stack(
                pos_tag_counts, ax=self.ax, labels=list(self.labels_),
                ticks=self._pos_tags, colors=self.colors, colormap=self.colormap
            )
        else:
            xidx = np.arange(len(self._pos_tags))
            colors = resolve_colors(
                n_colors=len(self._pos_tags), colormap=self.colormap,
                colors=self.colors
            )
            self.ax.bar(
                xidx, pos_tag_counts[0], color=colors
            )

        return self.ax

    def finalize(self, **kwargs):
        """
        Finalize the plot with ticks, labels, and title

        Parameters
        ----------
        kwargs: dict
            generic keyword arguments.
        """
        # NOTE: not deduping here, so this is total, not unique
        self.ax.set_ylabel("Count")

        if self.frequency:
            self.ax.set_xlabel(
                "{} part-of-speech tags, sorted by frequency".format(
                    self.tagset_names[self.tagset]
                ))
        else:
            self.ax.set_xlabel(
                "{} part-of-speech tags".format(self.tagset_names[self.tagset])
            )

        # bar stack(helper) sets the ticks if stack is true
        if not self.stack:
            self.ax.set_xticks(range(len(self._pos_tags)))
            self.ax.set_xticklabels(self._pos_tags, rotation=90)

        self.set_title(
            "PosTag plot for {}-token corpus".format(
                (sum([sum(i.values()) for i in self.pos_tag_counts_.values()]))
            )
        )

    def poof(self, outpath=None, **kwargs):
        if outpath is not None:
            kwargs["bbox_inches"] = kwargs.get("bbox_inches", "tight")
        return super(PosTagVisualizer, self).poof(outpath, **kwargs)


##########################################################################
## Quick Method
##########################################################################

def postag(
    X,
    y=None,
    ax=None,
    tagset="penn_treebank",
    colormap=None,
    colors=None,
    frequency=False,
    stack=False,
    **kwargs
):

    """
    Display a barchart with the counts of different parts of speech
    in X, which consists of a part-of-speech-tagged corpus, which the
    visualizer expects to be a list of lists of lists of (token, tag)
    tuples.

    Parameters
    ----------
    X : list or generator
        Should be provided as a list of documents or a generator
        that yields a list of documents that contain a list of
        sentences that contain (token, tag) tuples.

    ax : matplotlib axes
        The axes to plot the figure on.

    tagset: string
        The tagset that was used to perform part-of-speech tagging.
        Either "penn_treebank" or "universal", defaults to "penn_treebank".
        Use "universal" if corpus has been tagged using SpaCy.

    colors : list or tuple of colors
        Specify the colors for each individual part-of-speech.

    colormap : string or matplotlib cmap
        Specify a colormap to color the parts-of-speech.

    frequency: bool {True, False}, default: False
        If set to True, part-of-speech tags will be plotted according to frequency,
        from most to least frequent.

    kwargs : dict
        Pass any additional keyword arguments to the PosTagVisualizer.

    Returns
    -------
    ax : matplotlib axes
        Returns the axes on which the PosTagVisualizer was drawn.
    """
    # Instantiate the visualizer
    visualizer = PosTagVisualizer(
        ax=ax, tagset=tagset, colors=colors, colormap=colormap,
        frequency=frequency, stack=stack, **kwargs
    )

    # Fit and transform the visualizer (calls draw)
    visualizer.fit(X, y=y, **kwargs)

    # Return the axes object on the visualizer
    return visualizer.ax

    