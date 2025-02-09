# yellowbrick.features
# Visualizers for feature analysis and diagnostics.
#
# Author:   Benjamin Bengfort <bbengfort@districtdatalabs.com>
# Created:  Mon Oct 03 21:30:18 2016 -0400
#
# Copyright (C) 2016 District Data Labs
# For license information, see LICENSE.txt
#
# ID: __init__.py [0f4b236] benjamin@bengfort.com $

"""
Visualizers for feature analysis and diagnostics.
"""

##########################################################################
## Imports
##########################################################################

## Hoist visualizers into the features namespace
from .pcoords import ParallelCoordinates, parallel_coordinates
from .radviz import RadialVisualizer, RadViz, radviz
from .rankd import Rank1D, rank1d, Rank2D, rank2d
from .jointplot import JointPlot, JointPlotVisualizer, joint_plot
from .pca import PCA, PCADecomposition, pca_decomposition
from .importances import FeatureImportances, feature_importances
from .rfecv import RFECV, rfecv
from .manifold import Manifold, manifold_embedding

# Alias the TargetType defined in yellowbrick.utils.target
from yellowbrick.utils.target import TargetType
