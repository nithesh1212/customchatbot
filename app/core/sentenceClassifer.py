import os
import pickle

from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from app.core.NLTKPreprocessor import NLTKPreprocessor


def identity(arg):
    """
    Simple identity function works as a passthrough.
    """
    return arg


def train(X, y, outpath=None, verbose=True):
    def build(X, y=None):
        print("In build")
        """
        Inner build function that builds a single model.
        """
        model = Pipeline([
            ('preprocessor', NLTKPreprocessor()),
            ('vectorizer', TfidfVectorizer(
                tokenizer=identity, preprocessor=None, lowercase=False)),
            ('clf', OneVsRestClassifier(LinearSVC()))])

        print("Before model.fit")

        model.fit(X, y)
        print("Model",model)
        return model

    # Label encode the targets
    print("X",X)
    print("Y",y)
    labels = preprocessing.MultiLabelBinarizer()
    print("Lables ",labels)
    y = labels.fit_transform(y)
    print("Y transofrm",y)
    model = build(X, y)
    model.labels_ = labels
    print("Model labels",model.labels_)

    if outpath:
        print("Inside outpath",outpath)
        print("")
        print("")
        try:
            with open(outpath, 'wb') as f:
                pickle.dump(model, f)
        except:
            print("In with open excetion")

            if verbose:
                print("Model written out to {}".format(outpath))

    return model


def predict(text, PATH):
    print("Inside Senetnce Classified predict")
    print("Path/////",PATH)
    try:
        with open(PATH, 'rb') as f:
            model = pickle.load(f)
            print("Model",model)
    except IOError:
        print("Inside error")
        return False

    yhat = model.predict([
        text
    ])
    print("yhat",yhat)
    if yhat.any():
        print("In yhat.any()")
        return {
            "class": model.labels_.inverse_transform(yhat)[0][0],
            "accuracy": 1
        }
    else:
        print("In else")
        return False
