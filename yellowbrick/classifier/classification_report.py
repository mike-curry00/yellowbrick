# yellowbrick.classifier.classification_report
# Visual classification report for classifier scoring.
#
# Author:   Rebecca Bilbro
# Author:   Benjamin Bengfort
# Author:   Neal Humphrey
# Author:   Allyssa Riley
# Author:   Larry Gray
# Created:  Wed May 3 18:15:42 2017 -0400
#
# Copyright (C) 2017 The scikit-yb developers
# For license information, see LICENSE.txt
#
# ID: classification_report.py [5388065] neal@nhumphrey.com $

"""
Visual classification report for classifier scoring.
"""

##########################################################################
## Imports
##########################################################################

import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support

from yellowbrick.style import find_text_color
from yellowbrick.style.palettes import color_sequence
from yellowbrick.exceptions import YellowbrickValueError
from yellowbrick.classifier.base import ClassificationScoreVisualizer

##########################################################################
## Classification Report
##########################################################################

PERCENT = "percent"
CMAP_UNDERCOLOR = "w"
CMAP_OVERCOLOR = "#2a7d4f"
SCORES_KEYS = ("precision", "recall", "f1", "support")


class ClassificationReport(ClassificationScoreVisualizer):
    """
    Classification report that shows the precision, recall, F1, and support scores
    for the model. Integrates numerical scores as well as a color-coded heatmap.

    Parameters
    ----------
    ax : Matplotlib Axes object
        The axis to plot the figure on.

    model : the Scikit-Learn estimator
        Should be an instance of a classifier, else the __init__ will
        return an error.  If the internal model is not fitted, it is fit when
        the visualizer is fitted, unless otherwise specified by ``is_fitted``.

    classes : a list of class names for the legend
        If classes is None and a y value is passed to fit then the classes
        are selected from the target vector.

    cmap : string, default: ``'YlOrRd'``
        Specify a colormap to define the heatmap of the predicted class
        against the actual class in the classification report.

    support: {True, False, None, 'percent', 'count'}, default: None
        Specify if support will be displayed. It can be further defined by
        whether support should be reported as a raw count or percentage.

    is_fitted : bool or str, default="auto"
        Specify if the wrapped estimator is already fitted. If False, the estimator
        will be fit when the visualizer is fit, otherwise, the estimator will not be
        modified. If "auto" (default), a helper method will check if the estimator
        is fitted before fitting it again.

    kwargs : dict
        Keyword arguments passed to the super class.

    Examples
    --------
    >>> from yellowbrick.classifier import ClassificationReport
    >>> from sklearn.linear_model import LogisticRegression
    >>> viz = ClassificationReport(LogisticRegression())
    >>> viz.fit(X_train, y_train)
    >>> viz.score(X_test, y_test)
    >>> viz.poof()

    Attributes
    ----------
    score_ : float
        Global accuracy score

    scores_ : dict of dicts
        Outer dictionary composed of precision, recall, f1, and support scores with
        inner dictionaries specifiying the values for each class listed.
    """

    def __init__(
        self,
        model,
        ax=None,
        classes=None,
        cmap="YlOrRd",
        support=None,
        is_fitted="auto",
        **kwargs
    ):
        super(ClassificationReport, self).__init__(
            model, ax=ax, classes=classes, is_fitted=is_fitted, **kwargs
        )

        self.support = support
        self.cmap = color_sequence(cmap)
        self.cmap.set_over(color=CMAP_OVERCOLOR)
        self.cmap.set_under(color=CMAP_UNDERCOLOR)
        self._displayed_scores = [key for key in SCORES_KEYS]

        if support not in {None, True, False, "percent", "count"}:
            raise YellowbrickValueError(
                "'{}' is an invalid argument for support, use None, True, "
                "False, 'percent', or 'count'".format(support)
            )

        if not support:
            self._displayed_scores.remove("support")

    def score(self, X, y=None, **kwargs):
        """
        Generates the Scikit-Learn classification report.

        Parameters
        ----------
        X : ndarray or DataFrame of shape n x m
            A matrix of n instances with m features

        y : ndarray or Series of length n
            An array or series of target or class values

        Returns
        -------

        score_ : float
            Global accuracy score
        """
        y_pred = self.predict(X)

        scores = precision_recall_fscore_support(y, y_pred)

        # Calculate the percentage for the support metric
        # and store the percent in place of raw support counts
        self.support_score_ = scores[-1]

        scores = list(scores)
        scores[-1] = scores[-1] / scores[-1].sum()

        # Create a mapping composed of precision, recall, F1, and support
        # to their respective values
        scores = map(lambda s: dict(zip(self.classes_, s)), scores)
        self.scores_ = dict(zip(SCORES_KEYS, scores))

        # Remove support scores if not required
        if not self.support:
            self.scores_.pop("support")

        self.draw()

        # Retrieve and store the score attribute from the sklearn classifier
        self.score_ = self.estimator.score(X, y)

        return self.score_

    def draw(self):
        """
        Renders the classification report across each axis.
        """
        # Create display grid
        cr_display = np.zeros((len(self.classes_), len(self._displayed_scores)))

        # For each class row, append columns for precision, recall, f1, and support
        for idx, cls in enumerate(self.classes_):
            for jdx, metric in enumerate(self._displayed_scores):
                cr_display[idx, jdx] = self.scores_[metric][cls]

        # Set up the dimensions of the pcolormesh
        # NOTE: pcolormesh accepts grids that are (N+1,M+1)
        X, Y = (
            np.arange(len(self.classes_) + 1),
            np.arange(len(self._displayed_scores) + 1),
        )
        self.ax.set_ylim(bottom=0, top=cr_display.shape[0])
        self.ax.set_xlim(left=0, right=cr_display.shape[1])

        # Set data labels in the grid, enumerating over class, metric pairs
        # NOTE: X and Y are one element longer than the classification report
        # so skip the last element to label the grid correctly.
        for x in X[:-1]:
            for y in Y[:-1]:

                # Extract the value and the text label
                value = cr_display[x, y]
                svalue = "{:0.3f}".format(value)

                # change the svalue for support (when y == 3) because we want
                # to label it as the actual support value, not the percentage
                if y == 3:
                    if self.support != PERCENT:
                        svalue = self.support_score_[x]

                # Determine the grid and text colors
                base_color = self.cmap(value)
                text_color = find_text_color(base_color)

                # Add the label to the middle of the grid
                cx, cy = x + 0.5, y + 0.5
                self.ax.text(cy, cx, svalue, va="center", ha="center", color=text_color)

        # Draw the heatmap with colors bounded by the min and max of the grid
        # NOTE: I do not understand why this is Y, X instead of X, Y it works
        # in this order but raises an exception with the other order.
        g = self.ax.pcolormesh(
            Y, X, cr_display, vmin=0, vmax=1, cmap=self.cmap, edgecolor="w"
        )

        # Add the color bar
        plt.colorbar(g, ax=self.ax)  # TODO: Could use self.fig now

        # Return the axes being drawn on
        return self.ax

    def finalize(self, **kwargs):
        """
        Finalize executes any subclass-specific axes finalization steps.
        The user calls poof and poof calls finalize.

        Parameters
        ----------
        kwargs: generic keyword arguments.

        """
        # Set the title of the classifiation report
        self.set_title("{} Classification Report".format(self.name))

        # Set the tick marks appropriately
        self.ax.set_xticks(np.arange(len(self._displayed_scores)) + 0.5)
        self.ax.set_yticks(np.arange(len(self.classes_)) + 0.5)

        self.ax.set_xticklabels(self._displayed_scores, rotation=45)
        self.ax.set_yticklabels(self.classes_)

        plt.tight_layout()  # TODO: Could use self.fig now


def classification_report(
    model,
    X,
    y=None,
    ax=None,
    classes=None,
    random_state=None,
    is_fitted="auto",
    **kwargs
):
    """Quick method:

    Displays precision, recall, F1, and support scores for the model.
    Integrates numerical scores as well as color-coded heatmap.

    This helper function is a quick wrapper to utilize the ClassificationReport
    for one-off analysis.

    Parameters
    ----------
    X  : ndarray or DataFrame of shape n x m
        A matrix of n instances with m features.

    y  : ndarray or Series of length n
        An array or series of target or class values.

    ax : matplotlib axes
        The axes to plot the figure on.

    model : the Scikit-Learn estimator
        Should be an instance of a classifier, else the __init__ will
        return an error.  If the internal model is not fitted, it is fit when
        the visualizer is fitted, unless otherwise specified by ``is_fitted``.

    classes : list of strings
        The names of the classes in the target

    random_state: integer
        The seed value for a random generator

    is_fitted : bool or str, default="auto"
        Specify if the wrapped estimator is already fitted. If False, the estimator
        will be fit when the visualizer is fit, otherwise, the estimator will not be
        modified. If "auto" (default), a helper method will check if the estimator
        is fitted before fitting it again.

    kwargs: dict
        Keyword arguments passed to the super class.

    Returns
    -------
    ax : matplotlib axes
        Returns the axes that the classification report was drawn on.
    """
    # Instantiate the visualizer
    visualizer = ClassificationReport(
        model=model, ax=ax, classes=classes, is_fitted=is_fitted, **kwargs
    )

    # Create the train and test splits
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )

    # Fit and transform the visualizer (calls draw)
    visualizer.fit(X_train, y_train, **kwargs)
    visualizer.score(X_test, y_test)

    # Return the visualizer
    return visualizer
