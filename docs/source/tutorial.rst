####################################
A-to-Z tutorial - example analysis
####################################


***********************************
Intro and recommendations
***********************************

In this A-to-Z tutorial, we are going to analyze two datasets step-by-step, with each analysis covering different aspects of using *RNAlysis*.

These analyses both focus on RNA sequencing data from nematodes, but the same principles can be applied to data from any organism.

****************************************
Analysis #1 - time series RNA sequencing
****************************************

The dataset
=================
We will start by analyzing XYZ. This dataset describes the mean expression level of each gene over the developmental stages of *C. elegans* nematodes.

Let's start by loading the dataset:

#TODO: PtrSc

Data preprocessing and exploratory data analysis
=================================================

Filter out lowly-expressed genes
---------------------------------

Examine variance in our data with Principal Component Analysis
---------------------------------------------------------------

Examine similarity between developmental stages
-------------------------------------------------

Compare the expression of specific genes over the developmental stages
-----------------------------------------------------------------------


Clustering analysis
====================

The simple approach - distance-based clustering with K-Means
--------------------------------------------------------------

Fine-tuning our approach - density-based clustering with HDBSCAN
-----------------------------------------------------------------

The complex approach - ensemble-based clustering with CLICOM
--------------------------------------------------------------


Enrichment analysis
====================


Running enrichment analysis
----------------------------

*******************************************
Analysis #2 - differential expression data
*******************************************

The dataset
=================
We will start by analyzing XYZ. This dataset describes...

Let's start by loading the dataset:

#TODO: PtrSc

Data filtering and visualization with Pipelines
=================================================

#TODO

Apply the Pipeline to our datasets
-----------------------------------

Visualizing and extracting gene set interesctions
===================================================

Create a Venn diagram
-----------------------

Extract the subsets we are interested in
-----------------------------------------

Enrichment analysis
====================

Define a background set
-------------------------

Define our custom enrichment attributes
----------------------------------------

Running enrichment analysis
----------------------------