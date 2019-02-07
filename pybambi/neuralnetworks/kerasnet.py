"""Keras neural net predictor.

This implements a Keras Sequential model (a deep MLP)

Author: Martin White (martin.white@adelaide.edu.au)
Date: December 2018

"""
import numpy
from pybambi.neuralnetworks.base import Predictor
from keras.models import Sequential
from keras.layers import Dense


class KerasNetInterpolation(Predictor):
    """Keras neural net interpolation.

    Returns the loglikelihood from a Keras neural net-based interpolator

    Trains a basic 3-layer neural network with 200 neurons per layer.

    Parameters
    ----------
    params:
        `numpy.array of` physical parameters to train on
        shape (ntrain, ndims)

    logL:
        `numpy.array` of loglikelihoods to learn
        shape (ntrain,)

    """

    def __init__(self, params, logL, split=0.8, model=None):
        """Construct predictor from training data."""
        super(KerasNetInterpolation, self).__init__(params, logL)

        # Shuffle the params and logL in unison
        # (important for splitting data into training and test sets)
        nparams = len(params)
        randomize = numpy.random.permutation(nparams)
        self.params = params[randomize]
        self.logL = logL[randomize]

        # Now split into training and test sets
        ntrain = int(split*nparams)
        params_training, params_test = numpy.split(self.params, [ntrain])
        logL_training, logL_test = numpy.split(self.logL, [ntrain])

        if model is None:
            model = self._default_architecture()

        self.model = model

        self.history = self.model.fit(params_training, logL_training,
                                       validation_data=(params_test, logL_test),
                                       epochs=100)


    def _default_architecture(self):
        # Create model
        model = Sequential()

        # Number of neurons in each hidden layer, could make this configurable?
        numNeurons = 200

        # Get number of input parameters
        # Note: if params contains extra quantities (ndim+others),
        # we need to change this
        n_cols = self.params.shape[1]

        # Add model layers, note choice of activation function (relu)
        # We will use 3 hidden layers and an output layer
        # Note: in a Dense layer, all nodes in the previous later connect
        # to the nodes in the current layer

        model.add(Dense(numNeurons, activation='relu', input_shape=(n_cols,)))
        model.add(Dense(numNeurons, activation='relu'))
        model.add(Dense(numNeurons, activation='relu'))
        model.add(Dense(1))

        # Now compile the model
        # Need to choose training optimiser, and the loss function
        model.compile(optimizer='adam', loss='mean_squared_error')

        return model

    def __call__(self, x):
        """Calculate proxy loglikelihood.

        Parameters
        ----------
        x:
            `numpy.array` of physical parameters to predict

        Returns
        -------
        proxy loglikelihood value(s)

        """
        x_ = numpy.atleast_2d(x)
        y = self.model.predict(x_)
        return numpy.squeeze(y)

    def uncertainty(self):
        """Returns an uncertainty value for the trained keras model

        Returns
        -------
        uncertainty value

        """
        test_loss = numpy.sqrt(self.history.history['val_loss'])

        return numpy.squeeze(test_loss[-1])
