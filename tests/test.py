from ml_fingerprint import main
import numpy as np
from sklearn.linear_model import LinearRegression

#Test to check if the decorator works when using ml-fingerprint as a package. It works!
#NOTE: It requires having the ml-fingerprint installed. Therefore it's not a good test, and it should be changed in the future.

#This test recreates the 2D linear regression model in VanderPlas' book, adds the decorator and tests if it has the foo() method.


# Create some data for the regression
rng = np.random.RandomState(1)

X = rng.randn(200, 2)
y = np.dot(X, [-2, 1]) + 0.1 * rng.randn(X.shape[0])

# fit the regression model
model = LinearRegression()
model.fit(X, y)

# create some new points to predict
X2 = rng.randn(100, 2)

# predict the labels
y2 = model.predict(X2)

#Adding the foo method
main.decorate_base_estimator()

#Checking if it works
model.foo()