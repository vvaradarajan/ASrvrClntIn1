#Program usess erasmus sieve to find the Gaps between prime numbers
#+918108015880

import math,sys
repeatPeriod = 1
primes=[]

def updatePrParams(npr,reset=False):
    global repeatPeriod,primes
    if reset:
        repeatPeriod = 1
        primes=[] 
    else:       
        primes.append(npr)
        repeatPeriod = repeatPeriod*npr


def getGapsOld(startPr,pattern):
    #algorithm:
    #startPr is the starting prime. pattern is the gaps in
    #candidate primes after the startPr.
    #pattern is the repeating sequence of gaps. The repeat period
    #is the product of all previous primes
    #The next pattern is generated from the new prime upto the 
    #repeat period
    def getNext(pattern,idx):
        #only the terms after the first one repeat (discovered by observation, but can be derived by summing the patters)
        l=len(pattern)
        if idx < l:
            retval=pattern[idx]
        else: retval = pattern[(idx-1)%(l-1) +1]
        #if retval ==1: return 2 #special case
        return retval

    def findCandidatePrimes(pr,repeatPeriod,pattern):
        #Takes a pattern, finds the candidate primes
        #The algorithm is to start repeat at the idx from where it sums to the repeatPeriod
        #For some reason this is just dropping the first term in the pattern
        caPrs=[]
        acc=pr
        for g in pattern:
            acc +=g
            caPrs.append(acc)
        return caPrs
    
    # #test
    # p=[2,2,4]
    # x=[]
    # for i in range(10): x.append(getNext(p,i))
    # print(f'p={p}, x={x}')
    # exit(0)
    # #end test
    nextPrime=startPr+pattern[0]
    updatePrParams(nextPrime)
    endPatternAt=nextPrime+repeatPeriod
    newp=[]
    gap=0
    i=1 #start at the next candidate
    cp = nextPrime
    while True:
        cp +=getNext(pattern,i) #keep track of where we are in numbers
        gap += getNext(pattern,i) 
        if cp % nextPrime == 0:
            pass
        else:
            newp.append(gap)
            gap=0
        i+=1
        if cp > endPatternAt: break
    # print(f'Next Prime: {nextPrime}')
    # print(f'Old pattern: {pattern}')
    # print(f'new pattern: length of repeating pattern: {len(newp)}\n:{newp}')
    # print(f'Candidate Primes: {findCandidatePrimes(nextPrime,repeatPeriod,newp)}')
    return nextPrime,newp

def getGaps(startPr,pattern):
    #calculate the new values
    nextPrime=startPr+pattern[0]
    updatePrParams(nextPrime)
    #spread pattern to cover repeat period
    repPart=pattern[1:]
    repSum= sum(repPart)
    repTimes = math.ceil(repeatPeriod/repSum)
    tPattern=[]
    for i in range(repTimes):tPattern.extend(repPart)
    #eliminate to derive new pattern
    acc = nextPrime
    np2 = nextPrime*nextPrime
    idxToEliminate=[]
    # ncp=1
    # for idx,g in enumerate(tPattern):
    #     acc +=g
    #     if acc < np2: continue
    #     if acc % nextPrime==0:
    #         idxToEliminate.append(idx)
    #         ncp +=1
    #         np2 = nextPrime*(nextPrime+ncp)
    # print(f'idxToEliminate: {idxToEliminate}, tPattern: {tPattern}')
    ###########Trial section #################
    ngp = 0
    npPlus=nextPrime
    for idx in range(len(tPattern)):
        acc +=tPattern[idx]
        if acc == np2:
            idxToEliminate.append(idx)
            #Find the next np2 (a guess)
            npPlus +=tPattern[ngp]
            if nextPrime==5: print(f'npPlus: {npPlus}')
            np2= nextPrime*npPlus
            ngp +=1
        else: continue
    ##################
    for dIdx in idxToEliminate:
        if dIdx==len(tPattern) -1:
            tPattern[dIdx] += tPattern[0]
        else:
            tPattern[dIdx] +=tPattern[dIdx+1]
            tPattern[dIdx+1]=-1 #marker means to remove
    #print(f'nextPrime: {nextPrime}, repeatPeriod = {repeatPeriod}; nPattern= {tPattern}')
    tPattern = [g for g in tPattern if g>0]
    return nextPrime,tPattern
    
    

def findPrimesBelowN(N):
    #Algorithm:
    #1. Find the candidate primes for the lowest P where P > sqrt(N)
    #2. Count the candidate primes below N (and add the number of primes before P)
    primes=[]
    nxtp,newp=1,[1,1]
    lowestP = math.ceil(math.sqrt(N))
    print(f'lowestP = {lowestP}')

    while True:
        nxtp,newp=getGaps(nxtp,newp)
        print(f'nxtp = {nxtp}')
        primes.append(nxtp)
        if nxtp > lowestP: break
    #accumulate the candidate primes less than N into primes
    acc=nxtp
    for g in newp:
        acc +=g
        if acc > N: break
        primes.append(acc)
    print(f'There are {len(primes)} primes below {N}:\n{primes}')

def test(t):
    match t:
        case 1:
            args = sys.argv
            print(f'args={args}')
            if len(args)>= 2: N= int(args[1])
            else: N=100
            findPrimesBelowN(N)
        case 2:
            updatePrParams(None,reset=True)
            print('*'*20)
            nxtp,newp = (1,[1,1])
            for i in range(3):
                nxtp,newp = getGaps(nxtp,newp)
                print(f'nxtp = {nxtp}, newp={newp}')
            updatePrParams(None,reset=True)
            print('*'*20)
            nxtp,newp = (1,[1,1])
            for i in range(3):
                nxtp,newp = getGapsOld(nxtp,newp)
                print(f'nxtp = {nxtp}, newp={newp}')

        case 3:
            pattern=[1,1]
            pr = 1
            #find gap pattern for first 5 primes
            nxtp,newp = getGaps(1,pattern)
            nxtp,newp = getGaps(nxtp,newp)
            nxtp,newp = getGaps(nxtp,newp)
            nxtp,newp = getGaps(nxtp,newp)
            nxtp,newp = getGaps(nxtp,newp)
            nxtp,newp = getGaps(nxtp,newp)

test(1)






