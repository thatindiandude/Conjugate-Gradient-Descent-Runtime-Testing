# Conjugate Gradient Descent Algorithm
# Testing runtime -- push results to SQLite 3 DB

import numpy as np
import sys
import math
import sqlite3 
import scipy
from scipy.sparse.linalg.isolve import _iterative
from scipy.sparse.linalg.isolve.utils import make_system
import scipy.sparse.linalg
import random

# override the conjugate gradient function from scipy
# to return iterations
_type_conv = {'f':'s', 'd':'d', 'F':'c', 'D':'z'}

def NumCGIterations(A, b, x0=None, tol=1e-14, maxiter=None, xtype=None, M=None, callback=None):
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

def CGSolution(A, b, x0=None, tol=1e-14, maxiter=None, xtype=None, M=None, callback=None):
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

    return postprocess(x), info

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
                Type varchar(100),
                MatrixSize INTEGER,
                NumUniqueEigenvals INTEGER,
                NumIterations INTEGER, 
                ConditionNumber REAL,
                CGvsActual varchar(100)
            )''')

## Validation of CGR Algorithm

def calcConditionNum(s):
    s.sort()
    return s[len(s)-1]/s[0]

def calcCGvsActual(A, b):
    actual = np.linalg.solve(A, b)
    cg = CGSolution(A, b)
    if (actual == "None"):
        return np.linalg.norm(cg[0])
    else: 
        return np.linalg.norm(actual - cg[0])

def cgr1():
    eigenvals = []
    for x in range(1,101):
        eigenvals.append(x)
        
    A = np.diag(eigenvals)
    Q = scipy.linalg.orth(np.random.randn(100, 100))
    A = np.mat(A)
    Q = np.mat(Q)
    A = np.transpose(Q)*A*Q

    b = np.ones((100,1))

    NumIterations = scipy.sparse.linalg.cg(A,b)
    print "CGR-1:" + str(NumIterations)

def cgr2():
    eigenvals = []
    for x in range(1,1001):
        eigenvals.append(x)

    #print eigenvals
    A = np.mat(np.diag(eigenvals))
    Q = np.mat(scipy.linalg.orth(np.random.randn(1000, 1000)))
    A = np.transpose(Q)*A*Q
    b = np.ones((1000, 1))
    NumIterations = scipy.sparse.linalg.cg(A,b)
    print "CGR-2: " + str(NumIterations)

def cgr3():
    v1 = np.ones((500,1))
    v1 = np.mat(v1)
    v2 = 2*v1
    v2 = np.mat(v2)
    v = np.concatenate((v1,v2))
    A = np.mat(np.diagflat(v))
    Q = np.mat(scipy.linalg.orth(np.random.randn(1000, 1000)))
    A = np.transpose(Q)*A*Q
    b = np.ones((1000, 1))
    NumIterations = scipy.sparse.linalg.cg(A,b)
    print "CGR-3: " + str(NumIterations)

def normal(ExperimentNo):   
    matrix_size = 1
    while (matrix_size <= 10000):
        loc = 10
        scale = 1
        for j in range(0,3):
            s = np.random.normal(loc, scale, matrix_size)
            s = s.round()
            ConditionNumber = calcConditionNum(s)

            b = np.ones((matrix_size, 1))
            A = np.mat(np.diag(s))
            Q = np.mat(scipy.linalg.orth(np.random.randn(matrix_size, matrix_size)))
            A = np.transpose(Q)*A*Q
            
            CGvsActual = calcCGvsActual(A,b)
            CGvsActual = str(CGvsActual)
            NumIterations = scipy.sparse.linalg.cg(A,b) 
            NumUniqueEigenvals = StoreSpectrum(s, ExperimentNo)
            print ExperimentNo
            cur.execute('''INSERT INTO Experiments(ExperimentNo, Type, MatrixSize, NumUniqueEigenvals, NumIterations, ConditionNumber, CGvsActual) VALUES (?,?,?,?,?,?,?)''', (ExperimentNo, "Normal", matrix_size, NumUniqueEigenvals, NumIterations, ConditionNumber, CGvsActual))
            db.commit()
            ExperimentNo+=1
        matrix_size+=100
    print "Normal Done"

def uniform(ExperimentNo):
    matrix_size = 1
    while (matrix_size <= 10000):
        low = 0
        high = 20
        for j in range(0,5):
            s = np.random.uniform(low, high, matrix_size)
            s = s.round()
            ConditionNumber = calcConditionNum(s)

            b = np.ones((matrix_size, 1))
            A = np.mat(np.diag(s))
            Q = np.mat(scipy.linalg.orth(np.random.randn(matrix_size, matrix_size)))
            A = np.transpose(Q)*A*Q

            CGvsActual = calcCGvsActual(A,b)
            CGvsActual = str(CGvsActual)
            NumIterations = scipy.sparse.linalg.cg(A,b) # overriden
            NumUniqueEigenvals = StoreSpectrum(s, ExperimentNo)
            print ExperimentNo
            cur.execute('''INSERT INTO Experiments(ExperimentNo, Type, MatrixSize, NumUniqueEigenvals, NumIterations, ConditionNumber, CGvsActual) VALUES (?,?,?,?,?,?,?)''', (ExperimentNo, "Uniform", matrix_size, NumUniqueEigenvals, NumIterations, ConditionNumber, CGvsActual))
            db.commit()
            ExperimentNo+=1
        matrix_size+=100
    print "Uniform done"

def exponential(ExperimentNo): 
    matrix_size = 1
    while (matrix_size <= 10000):
        scale = 1
        for j in range(0,5):
            s = np.random.exponential(scale, matrix_size)
            s = s.round()
            ConditionNumber = calcConditionNum(s)
            
            b = np.ones((matrix_size, 1))
            A = np.mat(np.diag(s))
            Q = np.mat(scipy.linalg.orth(np.random.randn(matrix_size, matrix_size)))
            A = np.transpose(Q)*A*Q
            
            CGvsActual = calcCGvsActual(A,b)
            CGvsActual = str(CGvsActual)
            NumIterations = scipy.sparse.linalg.cg(A,b) # overriden
            NumUniqueEigenvals = StoreSpectrum(s, ExperimentNo)
            print ExperimentNo
            cur.execute('''INSERT INTO Experiments(ExperimentNo, Type, MatrixSize, NumUniqueEigenvals, NumIterations, ConditionNumber, CGvsActual) VALUES (?,?,?,?,?,?,?)''', (ExperimentNo, "Exponential", matrix_size, NumUniqueEigenvals, NumIterations, ConditionNumber, CGvsActual))
            db.commit()
            ExperimentNo+=1
        matrix_size+=100
    print "Exponential Done"

def logistic(ExperimentNo): 
    matrix_size = 1
    while (matrix_size <= 10000):
        loc = 10
        scale = 1
        for j in range(0,5):
            s = np.random.logistic(loc, scale, matrix_size)
            s = s.round()
            ConditionNumber = calcConditionNum(s)

            b = np.ones((matrix_size, 1))
            A = np.mat(np.diag(s))
            Q = np.mat(scipy.linalg.orth(np.random.randn(matrix_size, matrix_size)))
            A = np.transpose(Q)*A*Q
            
            CGvsActual = calcCGvsActual(A,b)
            CGvsActual = str(CGvsActual)
            NumIterations = scipy.sparse.linalg.cg(A,b) # overriden
            NumUniqueEigenvals = StoreSpectrum(s, ExperimentNo)
            print ExperimentNo
            cur.execute('''INSERT INTO Experiments(ExperimentNo, Type, MatrixSize, NumUniqueEigenvals, NumIterations, ConditionNumber, CGvsActual) VALUES (?,?,?,?,?,?,?)''', (ExperimentNo, "Logistic", matrix_size, NumUniqueEigenvals, NumIterations, ConditionNumber, CGvsActual))
            db.commit()
            ExperimentNo+=1
        matrix_size+=100
    print "Logistic Done"

normal(ExperimentNo)
uniform(ExperimentNo)
exponential(ExperimentNo)
logistic(ExperimentNo)
db.close()