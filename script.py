# Conjugate Gradient Descent Algorithm
# Testing runtime -- push results to SQLite 3 DB

import numpy as np
import sys
import math
import sqlite3 
from scipy.sparse.linalg.isolve import _iterative
from scipy.sparse.linalg.isolve.utils import make_system
import scipy.sparse.linalg

# override the conjugate gradient function from scipy
# to return iterations
_type_conv = {'f':'s', 'd':'d', 'F':'c', 'D':'z'}

def NumCGIterations(A, b, x0=None, tol=1e-12, maxiter=None, xtype=None, M=None, callback=None):
    A,M,x,b,postprocess = make_system(A,M,x0,b,xtype)

    n = len(b)
    if maxiter is None:
        maxiter = n*10

    matvec = A.matvec
    psolve = M.matvec
    ltr = _type_conv[x.dtype.char]
    revcom = getattr(_iterative, ltr + 'cgrevcom')
    stoptest = getattr(_iterative, ltr + 'stoptest2')

    resid = tol
    ndx1 = 1
    ndx2 = -1
    work = np.zeros(4*n,dtype=x.dtype)
    ijob = 1
    info = 0
    ftflag = True
    bnrm2 = -1.0
    iter_ = maxiter
    while True:
        olditer = iter_
        x, iter_, resid, info, ndx1, ndx2, sclr1, sclr2, ijob = \
           revcom(b, x, work, iter_, resid, info, ndx1, ndx2, ijob)
        if callback is not None and iter_ > olditer:
            callback(x)
        slice1 = slice(ndx1-1, ndx1-1+n)
        slice2 = slice(ndx2-1, ndx2-1+n)
        if (ijob == -1):
            if callback is not None:
                callback(x)
            break
        elif (ijob == 1):
            work[slice2] *= sclr2
            work[slice2] += sclr1*matvec(work[slice1])
        elif (ijob == 2):
            work[slice1] = psolve(work[slice2])
        elif (ijob == 3):
            work[slice2] *= sclr2
            work[slice2] += sclr1*matvec(x)
        elif (ijob == 4):
            if ftflag:
                info = -1
                ftflag = False
            bnrm2, resid, info = stoptest(work[slice1], b, bnrm2, tol, info)
        ijob = 2

    if info > 0 and iter_ == maxiter and resid > tol:
        # info isn't set appropriately otherwise
        info = iter_

    return iter_

scipy.sparse.linalg.cg = NumCGIterations

# spectra consolidation
def StoreSpectrum (s, ExperimentNo): 
    SpectrumWithAlMu = {}
    for num in s: 
        if (num in SpectrumWithAlMu.keys()):
            SpectrumWithAlMu[num] += 1
        else: 
            SpectrumWithAlMu[num] = 1
    cur.execute('''DROP TABLE IF EXISTS SpectrumWithAlMu''' + str(ExperimentNo))
    cur.execute('''CREATE TABLE SpectrumWithAlMu''' + str(ExperimentNo) + '''(ExperimentNo INTEGER, Eigenvalue INTEGER, AlMu INTEGER)''')
    for eigenvalue in SpectrumWithAlMu:
        cur.execute('''INSERT INTO SpectrumWithAlMu''' + str(ExperimentNo) + '''(ExperimentNo, Eigenvalue, AlMu) VALUES(?,?,?)''', (ExperimentNo, eigenvalue, SpectrumWithAlMu[eigenvalue]))
        db.commit()
    return len(SpectrumWithAlMu.keys())


# globals
error = sys.maxint
ExperimentNo = 0

# create and connect to DB
db = sqlite3.connect('test.db')
cur = db.cursor()
cur.execute('''DROP TABLE IF EXISTS Experiments''')
cur.execute('''CREATE TABLE IF NOT EXISTS Experiments(
                ExperimentNo INTEGER,
                ClusterorDistribution varchar(100),
                Type varchar(100),
                MatrixSize INTEGER,
                NumUniqueEigenvals INTEGER,
                NumIterations INTEGER
            )''')

## CREATE MATRICES
# execute every experiment from 1 to 10,000

# -- CLUSTERS -- 

# -- DISTRIBUTIONS -- 

# Normal
matrix_size = 1
while (matrix_size <= 1000):
    loc = 10
    scale = 1
    for j in range(0,5):
        s = np.random.normal(loc, scale, matrix_size)
        s = s.round()
        b = np.random.random_integers(0, high=matrix_size, size=(matrix_size, 1.))
        A = np.diag(s)
        NumIterations = scipy.sparse.linalg.cg(A,b) # overriden
        NumUniqueEigenvals = StoreSpectrum(s, ExperimentNo)
        print ExperimentNo
        cur.execute('''INSERT INTO Experiments(ExperimentNo, ClusterorDistribution, Type, MatrixSize, NumUniqueEigenvals, NumIterations) VALUES (?,?,?,?,?,?)''', (ExperimentNo, "Distribution", "Normal", matrix_size, NumUniqueEigenvals, NumIterations))
        db.commit()
        ExperimentNo+=1
    matrix_size+=10

print "Normal Done"
# Uniform
matrix_size = 1
while (matrix_size <= 1000):
    low = 0
    high = 20
    for j in range(0,5):
        s = np.random.uniform(low, high, matrix_size)
        s = s.round()
        b = np.random.random_integers(0, high=matrix_size, size=(matrix_size, 1.))
        A = np.diag(s)
        NumIterations = scipy.sparse.linalg.cg(A,b) # overriden
        NumUniqueEigenvals = StoreSpectrum(s, ExperimentNo)
        print ExperimentNo
        cur.execute('''INSERT INTO Experiments(ExperimentNo, ClusterorDistribution, Type, MatrixSize, NumUniqueEigenvals, NumIterations) VALUES (?,?,?,?,?,?)''', (ExperimentNo, "Distribution", "Uniform", matrix_size, NumUniqueEigenvals, NumIterations))
        db.commit()
        ExperimentNo+=1
    matrix_size+=10

print "Uniform Done"
# Exponential
matrix_size = 1
while (matrix_size <= 1000):
    scale = 1
    for j in range(0,5):
        s = np.random.exponential(scale, matrix_size)
        s = s.round()
        b = np.random.random_integers(0, high=matrix_size, size=(matrix_size, 1.))
        A = np.diag(s)
        NumIterations = scipy.sparse.linalg.cg(A,b) # overriden
        NumUniqueEigenvals = StoreSpectrum(s, ExperimentNo)
        print ExperimentNo
        cur.execute('''INSERT INTO Experiments(ExperimentNo, ClusterorDistribution, Type, MatrixSize, NumUniqueEigenvals, NumIterations) VALUES (?,?,?,?,?,?)''', (ExperimentNo, "Distribution", "Exponential", matrix_size, NumUniqueEigenvals, NumIterations))
        db.commit()
        ExperimentNo+=1
    matrix_size+=10

print "Exponential Done"
# Logistic 
matrix_size = 1
while (matrix_size <= 1000):
    loc = 10
    scale = 1
    for j in range(0,5):
        s = np.random.logistic(loc, scale, matrix_size)
        s = s.round()
        b = np.random.random_integers(0, high=matrix_size, size=(matrix_size, 1.))
        A = np.diag(s)
        NumIterations = scipy.sparse.linalg.cg(A,b) # overriden
        NumUniqueEigenvals = StoreSpectrum(s, ExperimentNo)
        print ExperimentNo
        cur.execute('''INSERT INTO Experiments(ExperimentNo, ClusterorDistribution, Type, MatrixSize, NumUniqueEigenvals, NumIterations) VALUES (?,?,?,?,?,?)''', (ExperimentNo, "Distribution", "Logistic", matrix_size, NumUniqueEigenvals, NumIterations))
        db.commit()
        ExperimentNo+=1
    matrix_size+=10

print "Logistic Done. We're done here...check your database"
#count, bins, ignored = plt.hist(s, bin=50)


#while (error > epsilon): 
db.close()
