from sklearn.linear_model import LinearRegression
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.svm import SVC

def vanderplas_regression():
    #Create the model
    model = LinearRegression()
    # Create some data for the regression
    rng = np.random.RandomState(1)
    X = rng.randn(200, 2)
    y = np.dot(X, [-2, 1]) + 0.1 * rng.randn(X.shape[0])
    # fit the regression model
    model.fit(X, y)
    # create some new points to predict
    X2 = rng.randn(100, 2)
    # predict the labels
    y2 = model.predict(X2)
    
    return model

def vanderplas_classifier():
    # create 50 separable points
    X, y = make_blobs(n_samples=50, centers=2,
                    random_state=0, cluster_std=0.60)

    # fit the support vector classifier model
    clf = SVC(kernel='linear')
    clf.fit(X, y)

    # create some new points to predict
    X2, _ = make_blobs(n_samples=80, centers=2,
                    random_state=0, cluster_std=0.80)
    X2 = X2[50:]

    # predict the labels
    y2 = clf.predict(X2)
    return clf