from sklearn.linear_model import LinearRegression
from sklearn.linear_model import LogisticRegression
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.svm import SVC
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import csv
import pandas as pd


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

def rain_classifier():
    '''
    Linear classifier that predicts if it will rain tomorrow.
    The dataset is taken from Kaggle and can be found here:
    https://www.kaggle.com/jsphyg/weather-dataset-rattle-package
    It consists of daily weather data in australian cities, and whether
    it rained the next day or not.

    Returns
    -------
    model : sklearn.linear_model.LogisticRegression
        The classifier model, already trained and tested.
    score : float
        Fraction of test data that was correctly predicted.
    '''
    dataset = pd.read_csv('datasets/weatherAUS.csv')

    # Drop the RISK_MM column following the dataset owner recomendation for classifiers.
    dataset.drop('RISK_MM', axis=1, inplace=True)

    # Dividing columns in numerical and categorical
    categorical = []
    numerical = []
    for col in dataset.columns:
        if dataset.dtypes[col] == 'O':
            categorical.append(col)
        else:
            numerical.append(col)

    # Convert Date to separate year, month and day values
    dataset['Year'] = pd.to_datetime(dataset['Date']).dt.year
    dataset['Month'] = pd.to_datetime(dataset['Date']).dt.month
    dataset['Day'] = pd.to_datetime(dataset['Date']).dt.day
    # Drop Date column, as we don't need it anymore
    dataset.drop('Date', axis=1, inplace=True)
    categorical.remove('Date')
    numerical.append('Year')
    numerical.append('Month')
    numerical.append('Day')

    # Limiting all numerical outliers to a maximum value, set to 3 interquantile ranges (IQR) starting from 75%.
    for col in numerical:
        IQR = dataset[col].quantile(0.75) - dataset[col].quantile(0.25)
        max_outlier = dataset[col].quantile(0.75) + (IQR * 3)
        #print(col + ", max: " + str(max_outlier) + ", count: " + str(np.where(dataset[col]>max_outlier, 1, 0).sum()))
        dataset[col] = np.where(dataset[col]>max_outlier, max_outlier, dataset[col])
    
    # Fill the NaN numerical values with median
    for col in numerical:
        col_median=dataset[col].median()
        dataset[col].fillna(col_median, inplace=True)
        
    # Fill the NaN categorical values with mode
    for col in categorical:
        dataset[col].fillna(dataset[col].mode()[0], inplace=True)

    # Setting Y value as whether if it will rain tomorrow or not, and dropping it from main dataset.
    Y = dataset['RainTomorrow']
    dataset.drop('RainTomorrow', axis=1, inplace=True)
    categorical.remove('RainTomorrow')


    # Setting X value as all the other columns, converting the categorical ones into dummy values 
    # Dummy values are binary columns for each category in the original column, for whether the row 
    # belongs to that category or not.
    X = dataset[numerical]
    list_X = [X]
    for col in categorical:
        list_X.append(pd.get_dummies(dataset[col]))
    X = pd.concat(list_X, axis=1)

    # Normalize all data
    cols = X.columns
    scaler = MinMaxScaler()
    X = scaler.fit_transform(X)
    X = pd.DataFrame(X, columns=[cols])

    # Split X and Y data into train and test, with a 70%/30% ratio.
    # This also randomizes the data order before splitting the top 70% and the last 30%.
    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.3, random_state = 0)

    # instantiate the model
    model = LogisticRegression(solver='liblinear', random_state=0)


    # fit the model
    model.fit(X_train, y_train)

    y_pred_test = model.predict(X_test)

    score = accuracy_score(y_test, y_pred_test)
    return model, score