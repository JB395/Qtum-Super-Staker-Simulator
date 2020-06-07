version = "2020-06-07"

# primary simulation parameters
# set for network weight 20 million, Delegate Weight 105k, and 10 UTXOs

numBlocks = 60750          # unless set by spacing difficulty file
                           # 675 blocks a day, 4725 a week, 20250 month, 246375 a year
numWallets = 1000          # number of wallets (nodes), 1 or 10 for fast results
startingBlock = 0          # unless set in spacing difficulty file

delegatedWeight = 105000   # weight of delegated UTXOs
numberOfStakingUTXOs = 10  # number of staking UTXOs
stakingUTXOSize = 150      # size of each staking UTXO

stakableWeight = numberOfStakingUTXOs * stakingUTXOSize # Wallet Weight of stakable UTXOs
stake = 0                  # current number staked
missedBlockRewards = 0     # missed block rewards

# print("stakableWeight =", stakableWeight)

# determine target multipliers for multiple runs
from array import *                     # for arrays

# targetMultipliers = array('i',\
#              [832, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000,\
#               11000, 12000, 13000, 14000, 15000, 16000, 17000, 18000, 19000,\
#               20000, 21000, 22000, 23000, 24000, 26000, 28000, 30000])

# targetMultipliers = array('i', [832, 2000, 3000, 4000, 5000])

targetMultipliers = array('i', [4000])

# targetMultipliers = array('i', [4000, 4000, 4000, 4000, 4000, 4000, 4000])

# targetMultipliers = array('i', [4000, 4000, 4000, 4000, 4000, 4000, 4000, 4000, 4000, 4000, 4000, 4000, 4000, 4000])


'''

Qtum Super Staker Simulator

Copyright (c) 2017-2020 Jackson Belove
Beta software, use at your own risk
Unpublished software, MIT License, free, open software for the Qtum Community

A program to use the SHA-256 hash function and algorithms from Qtum Mainnet
wallet software to explore retargeting, the network weight calculation and block spacing.
Runs a simulation using "steps" to replicate 16 second granularity in the PoS algorithm.
Uses SHA-265 hash and identical logic for block-by-block retargeting. Simulates wallet 
populations from 500 to 20000, and can run for any number of blocks.

Also, may run a replay of mainnet block spacing by reading in a file containing
the block spacing and difficulty for a number of blocks. In the case of running
a replay, simulated inputs are not used. The replay is used mainly to tune
parameters and logic related to calculating network weight.

Logs the peak number of steps (x 16 seconds for clock time) and the number
of blocks with 5x target spacing (> 640 seconds or ten minutes 40 seconds).

Can be set to make multiple runs while adjusting a parameter. Set paramValue to
the parameter being adjusted in each run. For example, to do 10 runs adjusting
the target multiplier starting at 1,000 with a step of 2,000 on each run, override
the target multiplier at the top of the parameter loop, and assign that value
to paramValue for print/logging. Each of these conditions must be setup before the top
and at the bottom of the parameter loop. An example output adjusting the target
multiplier value (for the next block difficulty):

  Run | tgt multplr | ave secs | >=640 blks | max secs | collisns
    0 |  35,000.000 |   128.16 |          0 |      512 |       16
    1 |  37,500.000 |   112.64 |          0 |      560 |       19
    2 |  40,000.000 |   128.40 |          1 |      784 |       19

"Slow block" is a block with a long spacing, > 20 minutes.

Program Summary

    set switches & parameters for simulation complexity
    if doing replay, read file for spacing and difficulty
    initialize log file
    set starting target, based on network weight and number of wallets
    load the wallets: uniform, random, simulated mainnet

    parameter loop - - - - - - - - - - - - - - - - - - - - - -
   /
   |   initialize variables for a single run 
   |
   |    block loop - - - - - - - - - - - - - - - - - - - - - -
   |   /
   |   |    step loop - - - - - - - - - - - - - - - - - - - -
   |   |   /
   |   |   |    target scaling after XX steps, if configured
   |   |   |
   |   |   |    wallet loop - - - - - - - - - - - - - - - - -
   |   |   |   /
   |   |   |   |    if doing simulation
   |   |   |   |
   |   |   |   |        check wallet[50] if return stake to Wallet Weight
   |   |   |   |                     
   |   |   |   |        if target < SHA256 hash of random variable * wallet weight
   |   |   |   |            block reward
   |   |   |   |            if wallet[50] commit stake, debit Wallet Weight
   |   |   |   |            
   |   |   |   |        (loop through all wallets, check for collisions)
   |   |   |   |
   |   |   |   |    else doing replay
   |   |   |   |        use block spacing and difficulty from file
   |   |   |   \_
   |   |   |  
   |   |   |    adjust the target
   |   |   |    print and log (if desired)   
   |   |   \_
   |   \_
   |
   |     print and log results for a run
   \_


Revisions

2020/06/07 Clean up, remove old code
2020/06/05 All new, repurposed from Qtum Simulator

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

To help readability, the simulator tries to use variable names (and provides
source code file name/line of code references) from the qtum-master clone, version 0.17.1.

The simulator can calculate the true values of various numbers, for comparison
to the values calculated by algorithms. Examples of these are true network weight
(the sum of all wallet weights) and true wallet weight, which is a moving
average of the weights of recent wallet winners, for comparison to the
network weight calculation derived from the target, which is literally a
"moving target".

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

Simulation Complexity

The simulator may be set to run with different levels of complexity, from
simple fixed default parameters, then adding various improvements, adding 
input data measured from mainnet, and trying various soft fork scenarios
(to come). Simulation complexity is set next, along with the relevant
simulation parameters.

'''

import random                           # for pseudo-random numbers

# 0. Baseline: use wallets of uniform weight for a total network weight of
#    n million coins, a fixed target, use Python random module with
#    useFixedSeed = True to give repeatable outputs, or useFixedSeed = False
#    to give different random inputs each run.

useFixedSeed = True  # has no effect for the Python secrets module

if useFixedSeed == True:                                  # COMPLEXITY SWITCH 0
    random.seed("The Blockchain Made Ready for Business") # for repeatability, if desired

# 1. Use the Python secrets module to generate cryptographically secure random numbers
#    to be hashed. Set useSecretsModule = True to use this module, False to use the Python
#    random module. Used in the wallet loop. useFixedSeed has no effect if
#    useSecretsModule = True

useSecretsModule = True

# 2. Retarget with each block based on the PeerCoin/Qtum dynamics. Set
#    useRetarget = True to adjust the difficulty for each new block.
#    Otherwise, use a fixed difficulty, which was manually tweaked in for
#    an approximate average of 8 steps (128 seconds). Used in the wallet
#    loop.

useRetarget = True    # adjust difficulty with each block

# 3. Offset sets block timing within the 16 second steps.  This gives a
#    normal distribution from the start of the 16 second steps,
#    based on measured mainnet behavior. Set useNormalDistributionForOffset = True.
#    Otherwise the block spacing is set the end of the 16 second steps (rounding up,
#    I think, which causes an off-by-one error in the block spacing). Normally this is
#    set to false, because that is how the software works with mainet wallets.
#    Used in the wallet loop.

useNormalDistributionForOffset = False
offsetFromStartOfStep = 5.0          # based on mainnet averages
standardDeviationWithinStep = 0.7    # based on mainnet timing

# 4. Wallet weights can be set for three different approaches:
#
#    "Uniform" - all wallets receive identical weights for a total true network
#        weight of 20,000,000, or whatever.
#
#    "Random" - normal distribution random weights between 100 and 29545 for
#        total true network weight of 15,043,623.
#
#    "Mainnet" - distribution of the 100 largest wallet on mainnet, plus
#         100 small wallets 1 to 100, with the rest mid-sized wallets for
#         total true network weight of 20 million. 

walletWeightDistribution = "Mainnet"      # "Uniform", "Random" or "Mainnet"

# 5. Reserved

# 6. The setting useDynamicWeights = True allows changing the wallet
#    weights during the simulation run to show some "big guys" joining and leaving
#    at preset blocks, to observe retargeting algorithm behavior and network response,
#    in particular, to check response time for various retargeting multipliers and
#    the response for "network weight" derived from an inverse moving average of the
#    target. Used at the top of the block loop.

useDynamicWeights = False

# 7. The setting useSpacingDifficultyFile = True allows replaying block spacing and
#   difficulty ripped from the blockchain, or files otherwise created to test
#   spacing and difficulty sequences.
#   If useSpacingDifficultyFile is set to True, then random timing from SHA-256 hash and
#   Normal Distribution for Offset are disabled. Search for the text "7777A" to see where
#   spacing is set from the file, and search for the text "7777B" to see where difficulty
#   is set from the file. If both of these are active, then there is a full replay of mainnet
#   actions, which can be used for testing Network Weight calculations, but says nothing about
#   the probability response of the simulator. Otherwise, either the spacing or difficulty
#   input can be commented out to use one or the other for various test scenarios. numBlocks is
#   set by the number of rows in the file. The file also sets the starting block number.

useSpacingDifficultyFile = False
spacing_difficulty_file_name = "spacing_difficulty.txt"       # file name

# 8. Set useTargetScaling = True to dynamically increase the target during a block.
#    Starting with step 16 (or other values), multiply the target by targetScalingFactor,
#    set below. This gives a gradual exponential increase in the target if a block is
#    getting slow. You can also set the targetScalingFactor to 1.0 to disable scaling.
#    Used at the top of the step loop to reset the target for that step.

useTargetScaling = False
targetScalingFactor = 1.05

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =            

                          # setup here for multiple runs
run = 0                   # set the number of runs, the outer parameter loop 
# runMax = 31               # set the number of runs, while paramValue can be changed for
                          # each run. Set to 1 for a single run, or n for multiple runs

                          # paramValue is incremented at the end of a run at the bottom
                          # of the parameter loop, to iterate through the values and
                          # display the results 
# paramValue = 832          # paramValue must be used to set a variable in the code

                          # the increment value for paramValue, added to paramValue at 
# paramIncrement = 1000     # the bottom of the parameter loop

           # "abcdefghijk"
paramLabel = "  min step " # up to 11 charactrers column label in the printed output to
                           # identify the parameter

'''
targetScalingFactor = 1.000
paramValue = targetScalingFactor
paramIncrement = 0.005              # increment at the bottom of the parameter loop
paramLabel = "trgtScFactr"          # limit to 11 characters, prints on display and logs
'''

'''
startingStep = 16                   # step to start the target scaling
paramValue = startingStep
paramIncrement = 2                  # increment at the bottom of the parameter loop
paramLabel = "startngStep"          # limit to 11 characters, prints on display and logs
'''

# consensus parameters, or constants from the bitcoin source code- - - - - - - - - - - - - - - 

nPowTargetTimespan = 16 * 60            # from chainparams.cpp, line 94
nPowTargetSpacing = 2 * 64              # from chainparams.cpp, line 95
nPoSInterval = 72                       # for GetPoSKernelPS() in blockchain.cpp line 107
COIN = 100000000                        # from amount.h line 14:
                                        # static const CAmount COIN = 100000000;

                            # // To decrease granularity of timestamp, Supposed to be 2^n-1
STAKE_TIMESTAMP_MASK = 15   # pos.h line 21: static const uint32_t STAKE_TIMESTAMP_MASK = 15; 

EASIEST_DIFFICULTY = 26959000000000000000000000000000000000000000000000000000000000000000
                                        # = ffff0000000000000000000000000000000000000000000000000000 in hex

startingDifficulty = 3400000            # starting value for the four 121 block moving averages
                                        # 30 million network weight 5693691
                                        # 20 million network weight 3409395, 3900000 128 seconds
                                        # 15 million 2824920

averageDifficulty = 0.0                 # average difficulty for every block                                        

everyTen = 0                            # counter to force result every 10 times through                                        

# printing and logging switches - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

enableLogging = False       # control logging of settings and final results
printBlockByBlock = False   # print out each new block, doubles the simulation duration
logBlockByBlock = False     # log each new block, turn this off if just interested in end summary

import hashlib                          # for SHA-256 hash algorithm
import secrets				# for cryptographically strong random numbers
from timeit import default_timer as timer
import os, sys                          # for file operations
import time
from time import localtime, strftime, sleep
from datetime import datetime
# import winsound                         # change on Linux machines
import math                             # for exp()

for i in range(1, 161):
    nActualSpacing = 16 * i
    # print(16 * i, math.exp(2 * (nActualSpacing - 128) / 4000))

# sys.exit()          

print("Qtum Super Staker Simulator, version", version)

# read in the spacing difficulty file - - - - - - - - - - - - - - - - - - - - - - - - - -
# comments line start with a "#"
# the first non-comment line gives the starting block number
# This file can be derived from the blockchain ripper or manually created:
'''
# starting block:
35600
128,2123451
16,2123452
1280,2123453
''' 

runMax = len(targetMultipliers)
paramValue = 1                          # get the first step
# paramValue = targetMultipliers[run]   # get the first target multiplier

# print("lenthof targetMultipliers[] =",len(targetMultipliers))
# sys.exit()

# print("useSpacingDifficultyFile 1", useSpacingDifficultyFile)


if useSpacingDifficultyFile == True:
    blockSpacing = []              # an array of block spacings in seconds
    blockDifficulty = []           # an array of difficulties
    gotBlockNumber = False
    numBlocks = 0

    try:
        blockSpacingFile = open(spacing_difficulty_file_name, 'r')  # check for success, or exit
    except:
        print("ERROR opening spacing difficulty file")
        print('The configuration file "spacing_difficulty.txt" must be in the same directory with QSBES')
        sys.exit()

    print("useSpacingDifficultyFile = True, loading spacing and difficulty for replay from file", spacing_difficulty_file_name)  

    for line in blockSpacingFile:
        data = line
        # print("data", data)

        if data[0] != "#":                   # skip comments     
            if gotBlockNumber == False:      # get block number from first non-comment line
                startingBlock = int(data)
                print("startingBlock number is", startingBlock)
                gotBlockNumber = True
            else:
                i = 0
                strSpacing = ""
                strDifficulty = ""
                
                while i < len(data):   # just grab the spacing
                    if data[i] != ",":
                        strSpacing += data[i]
                    else:
                        break
                    i += 1

                i += 1    

                while i < len(data):   # just grab the difficulty
                    strDifficulty += data[i]
                    i += 1

                # print(strSpacing, strDifficulty)

                if strSpacing == '\n':   # read to end of file
                    break
                
                spacing = int(strSpacing)
                difficulty = float(strDifficulty)

                # print(spacing, difficulty)
                    
                blockSpacing.append(spacing)
                blockDifficulty.append(difficulty)
                numBlocks += 1                # count the blocks from the file

    blockSpacingFile.close()

# print("useSpacingDifficultyFile 2", useSpacingDifficultyFile)    

start = timer()

nNetworkWeightList = array('f',(0.0,) * nPoSInterval) # an array for storing old difficulty moving average values
nStakesTimeList =    array('f',(0.0,) * nPoSInterval) # an array for storing old block spacing moving average values

stepCount =    array('f',(0.0,) * 21) # an array for counting the number of steps at each size
collisionCountByStep = array('i',(0,) * 21) # an array for counting collisions at each step


stakeTable = []         # make a table to commit and return stakes

for i in range(510):
    stakeTable.append(0)

# print("stakeTable[500] =", stakeTable[500])    

# For a comparison to network weight, the simulator can calculate an average of the true
# wallet weight of recent winning wallets. Use the same period nPosInterval

# trueWalletWeight = 0.0   # used to calculate a moving average for the true wallet weight
# trueWalletWeightList = array('f',(0.0,) * nPoSInterval) # an array for storing old moving average values
# trueWalletWeightListIndex = 0 # the index into the moving average array

averageNewNetworkWeight = 0.0  # used to calculate the average new network weight

# if numWallets < 500:
#     print("Use at least 500 wallets")
#     sys.exit()

logFileName = "qsbes.csv"  # logging file

tempStr = ""

if enableLogging == True:
    tempStr += "enableLogging = True, "
else:
    tempStr += "enableLogging = False, "

if printBlockByBlock == True:
    tempStr += "printBlockByBlock = True, "
else:
    tempStr += "printBlockByBlock = False, "
        
if logBlockByBlock == True:
    tempStr += "logBlockByBlock = True"
else:
    tempStr += "logBlockByBlock = False"

if useSpacingDifficultyFile == False:      # running a simulation with all these parameters
 
    if useSecretsModule == True:
        tempStr += "\nUsing Python secrets module for cryptographically strong random numbers"
    else:
        if useFixedSeed == True:
            tempStr += "\nUsing Python random module with fixed seed for repeatable pseudo-random numbers"
        else:
            tempStr += "\nUsing Python random module with random seed for pseudo-random numbers"

    if useRetarget == True:
        tempStr += "\nuseRetarget = True, retarget on every block"
    else:
        tempStr += "\nuseRetarget = False, use fixed target"
        
    if useNormalDistributionForOffset == True:
        tempStr += "\nuseNormalDistributionForOffset = True, use block times within the 16 second steps"
    else:
        tempStr += "\nuseNormalDistributionForOffset = False, use fixed block times at the start of the 16 second steps"
        
    if useTargetScaling == True:
        tempStr += "\nUsing target scaling, targetScalingFactor" + str(targetScalingFactor)

if walletWeightDistribution == "Uniform":
    tempStr += "\nLoading wallets with uniform weights based on total network weight"
elif walletWeightDistribution == "Random":
    tempStr += "\nLoading wallets with random weights based on total network weight"
elif walletWeightDistribution == "Mainnet":
    tempStr += "\nLoading wallets with Mainnet distribution"
else:
    print('ERROR: wallet weight distribution must be set to "Uniform", "Random", or "Mainnet"')
    sys.exit()

if useDynamicWeights == True:
    tempStr += "\nuseDynamicWeights = True, can change the weights of wallets during the simulation run"
else:
    tempStr += "\nuseDynamicWeights = False, wallet weights are fixed during the simulation run"

print(tempStr)

GMT = strftime("Starting %a %d %b %Y %H:%M:%S GMT", time.gmtime())  # GMT
print(GMT)            

# initialize log file - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if enableLogging == True:    
    GMT = strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())  # GMT
    # open log file in the format "QM_Log_DD_MMM_YYYY.csv"
    out_file_name_QSBES = 'QSBES_Log_'+GMT[5]+GMT[6]+'_'+GMT[8]+GMT[9]+GMT[10]+\
                    '_'+GMT[12]+GMT[13]+GMT[14]+GMT[15]+'.csv'
    
    print("Log file name =", out_file_name_QSBES) 
        
    try:
        outFileQSBES = open(out_file_name_QSBES, 'a')   # create or open log file for appending
        tempStr = 'QSBES version' + version
        outFileQSBES.write(tempStr)
        outFileQSBES.write('\n')
        
        # log starting time:
        tempStr = 'Starting' + '_' + GMT[17]+GMT[18]+GMT[20]+GMT[21]+',hours,GMT,'+\
                  GMT[5]+GMT[6]+'_'+GMT[8]+GMT[9]+GMT[10]+GMT[12]+GMT[13]+GMT[14]+GMT[15]
        outFileQSBES.write(tempStr)
        outFileQSBES.write('\n')
        time.sleep(0.01)
        tempStr = "wallets" + "," + str(numWallets) + "," + "blocks" + "," + str(numBlocks)
        outFileQSBES.write(tempStr)
        outFileQSBES.write('\n')
        time.sleep(0.01)

    except IOError:   # NOT WORKING
        print("QSBES ERROR: File didn't exist, open for appending")

# log simulation parameters - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# gonna run a whole lot of simulations, better log the simulation complexity settings
# be sure to close Excel before running the simulator, or the log file won't open (on a PC)

if enableLogging == True:

    if useSpacingDifficultyFile == False:      # doing simulation, not replay
    
        if useSecretsModule == True:
            tempStr = "Using Python secrets module for cryptographically strong random numbers\n"
        else:
            if useFixedSeed == True:
                tempStr = "Using Python random module with fixed seed for repeatable pseudo-random numbers\n"
            else:
                tempStr = "Using Python random module with random seed for pseudo-random numbers\n"

        outFileQSBES.write(tempStr)
        time.sleep(0.01)            

        if useRetarget == True:
            tempStr = "useRetarget = True, retarget on every block\n"
        else:
            tempStr = "useRetarget = False, use fixed target\n"
            
        outFileQSBES.write(tempStr)
        time.sleep(0.01)

        if useNormalDistributionForOffset == True:
            tempStr = "useNormalDistributionForOffset = True, use block times within the 16 second steps\n"
        else:
            tempStr = "useNormalDistributionForOffset = False, use fixed block times at the start of the 16 second steps\n"

        if useTargetScaling == True:
            tempStr = "Using target scaling, targetScalingFactor" + "," + str(targetScalingFactor) + "\n"
            outFileQSBES.write(tempStr)
            time.sleep(0.01)
    else:     # using spacing difficulty file for replay
        
        tempStr = "useSpacingDifficultyFile = True, loading spacing and difficulty for replay from file," + spacing_difficulty_file_name + "\n"
        outFileQSBES.write(tempStr)
        time.sleep(0.01)
        
    if walletWeightDistribution == "Uniform":
        tempStr = "Loading wallets with uniform weights based on total network weight\n"
    elif walletWeightDistribution == "Random":
        tempStr = "Loading wallets with random weights based on total network weight\n"
    elif walletWeightDistribution == "Mainnet":
        tempStr = "Loading wallets with Mainnet distribuition\n"
    else:
        tempStr = "Unknown wallet distribution\n"

    outFileQSBES.write(tempStr)
    time.sleep(0.01)

    outFileQSBES.write(tempStr)
    time.sleep(0.01)        

    if useDynamicWeights == True:
        tempStr = "useDynamicWeights = True, can change the weights of wallets during the simulation run\n"
    else:
        tempStr = "useDynamicWeights = False, wallet weights are fixed during the simulation run\n"

    outFileQSBES.write(tempStr)
    time.sleep(0.01)    

    outFileQSBES.write(tempStr)
    time.sleep(0.01)    
        
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# print("useSpacingDifficultyFile 3", useSpacingDifficultyFile)

# starting targets based on trial and error with useRetarget = False to produce an
# average of 8 steps = 128 seconds, of course this is dependent on the network weight

if walletWeightDistribution == "Uniform":                 # COMPLEXITY SWITCH 4
    
    if numWallets == 500:
        target =      10000000000000000000000000000000000000000000000000000000000000
    elif numWallets == 1000:
        target =      6900000000000000000000000000000000000000000000000000000000000      
    elif numWallets == 5000:
        target =      4000000000000000000000000000000000000000000000000000000000000
    elif numWallets == 10000:
        target =      3100000000000000000000000000000
    elif numWallets <= 10:      # trueNetworkWeight 2000000
        target =      6900000000000000000000000000000000000000000000000000000000000
    else:
        target =      10000000000000000000000000000000000000000000000000000000000000
        
else:  # using non uniform wallet weights
    
    if numWallets == 500:       # 500 wallets, trueNetworkWeight 13409463 
        target =      10000000000000000000000000000000000000000000000000000000000000 
    elif numWallets == 1000:
        target =      6900000000000000000000000000000000000000000000000000000000000
                                # 4.73E60, 1000 wallets, true network weight 29943463
                                # 7.19E60, 1000 wallets, true network weight 20103463
                                # 9.50E60, 1000 wallets, true network weight 15008923 
                                # 1.11E61, 1000 wallets, true network weight 12668463
                                
    elif numWallets == 2000:    # trueNetworkWeight 14724932  
        target =      9880000000000000000000000000000000000000000000000000000000000    
    elif numWallets == 3000:    # trueNetworkWeight 16220932  
        target =      8310000000000000000000000000000000000000000000000000000000000                                                                                
    elif numWallets == 5000:    # trueNetworkWeight 19212932
        target =      7120000000000000000000000000000000000000000000000000000000000 
    elif numWallets == 10000:   # trueNetworkWeight 60755463
        target =       780000000000000000000000000000
    elif numWallets <= 10:      # trueNetworkWeight 2000000
        target =      6900000000000000000000000000000000000000000000000000000000000

startingTarget = target      # used to reset the target if scaling

# go ahead and preload these averaging arrays with default values, this is a KLUDGE
# since we don't really have the blockchain to read like "real" wallets
# but gets to a normal value sooner in the simulation or replay

for i in range(nPoSInterval):   
    dDiff = EASIEST_DIFFICULTY / target
    nNetworkWeightList[i] = dDiff * 4294967296
    nStakesTimeList[i] = nPowTargetSpacing           # nominally 128 seconds
    
walletStaking = []
for i in range(numWallets):
    walletStaking.append(1)      # initialize all wallets to be staking
    
'''
load wallets with individual weights, if not using uniform default set above        

  0 to 99   Big guys, 1.9 million to 13k (https://qtumexplorer.io/misc/biggest-miners on 10/2/2017)
  100 to 199   Little guys, 1 to 100 coins
  200 - numWallets normal distribution, mean = 2,000, sd = ???
  
  5,000 may be a realistic lifetime maximum, due to pools. Currently BTC has about
  10,000 nodes, and ETH has about 21,000.

'''
if numWallets <= 10:
    walletWeight = []
    for i in range(numWallets): # initialize all wallets for a network weight 20 million
            walletWeight.append(int(20000000/numWallets))
    
else:

    if walletWeightDistribution == "Uniform":  #       COMPLEXITY SWITCH 4
        walletWeight = []
        for i in range(numWallets): # initialize all wallets for a network weight 4 million
            walletWeight.append(int(2000000/numWallets))

    elif walletWeightDistribution == "Random":
        walletWeight = []
        for i in range(numWallets):
            walletWeight.append(random.randint(100,29545))
        
    elif walletWeightDistribution == "Mainnet":
        # wallets 0..99, the big guys, 19276431 total as of November 27, 2019
        walletWeight = array('i',\
            [10159440, 1476298, 1026613, 927736, 897533, 475786, 446616, 226317, 173171, 156778,\
            131622, 130950, 118766, 115182, 104692, 102129, 90991, 89872, 87762, 81911,\
            80440, 78336, 59883, 59304, 57548, 55710, 51245, 51186, 50856, 49223,\
            48100, 47661, 45319, 44475, 44429, 44255, 43559, 42304, 41968, 37544,\
            36946, 34971, 33418, 33117, 32502, 32244, 31448, 30447, 30126, 27903,\
            27683, 26492, 25504, 25357, 25338, 24912, 24597, 24465, 24233, 24032,\
            23819, 23519, 23379, 22867, 22452, 22261, 22204, 22035, 21805, 21561,\
            21040, 20201, 20168, 19485, 18685, 18308, 17657, 17402, 16961, 16164,\
            16044, 15767, 15182, 14226, 14044, 13816, 13663, 13181, 11700, 11647,\
            11406, 11219, 11191, 10987, 10978, 9926, 9278, 8293, 7996, 4669])
        
        # the little guys, just load them up with 1..100, 5050 total
        for i in range(100):
            walletWeight.append(i + 1)
                
        else:   # just fill it out with medium sized guys, 3920400 total
            for i in range(numWallets - 200):
                walletWeight.append((200 +i * 24) % 1810)     # 1000 wallets 30 million ((12500 + i *24) % 100000
                                                              # 1000 wallets 20 million ((200 +i * 24) % 19300 
                                                              # 1000 wallets 15 million 7470
                                                              # 1000 wallets 12.7 million 1000
                                                              # 5000 wallets 19.2 million 3000
                                                              # 2000 wallets 17.02 million 3000 + i * 24) % 5500
                #print("wallet", i, walletWeight[i])                                              
    else:
        print("ERROR: need to specify Uniform, Random, or Mainnet for wallet weight distribution")
        sys.exit()

trueNetworkWeight = 0

for i in range(numWallets):   
    trueNetworkWeight += walletWeight[i]

walletWeight[200] += 20000000 - trueNetworkWeight           # just top up to 20 million even

# setup our special wallet for delegated "offline staking", at position 50, in the middle of the "big guys"

walletWeight[50] = delegatedWeight + stakableWeight 
print("delegatedWeight =", delegatedWeight, "staking UTXOs number =", numberOfStakingUTXOs, "staking UTXO size =", stakingUTXOSize, "staking UTXO weight =", stakableWeight)
print("walletWeight[50] =", walletWeight[50])

trueNetworkWeight = 0

for i in range(numWallets):   
    trueNetworkWeight += walletWeight[i]

print("trueNetworkWeight", trueNetworkWeight)

# sys.exit()

# trueNetworkWeight = 0

# for i in range(numWallets):   
#     trueNetworkWeight += walletWeight[i]

# print("trueNetworkWeight", trueNetworkWeight)

if enableLogging == True:
    tempStr = "trueNetworkWeight," + str(trueNetworkWeight)
    outFileQSBES.write(tempStr)
    outFileQSBES.write('\n')
    time.sleep(0.01)

    if logBlockByBlock == True:  # print some column labels
        tempStr = "block,wallet,true network weight,network weight,new network weight,target,spacing,difficulty\n"
        outFileQSBES.write(tempStr)
        time.sleep(0.01) 

# sys.exit()

print("Wallets", numWallets, "blocks", numBlocks, "startingBlock", startingBlock, "runs", runMax)

if useSpacingDifficultyFile == True:
    print("Running replay - - - - - - - - - - - - - - - - - - - - - - - -")
else:    
    print("Running simulation - - - - - - - - - - - - - - - - - - - - - - - -")
    print("block, wallet weight")

# walletStaking[0] = 0  # turn off the big guy

# parameter loop - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# note, targets, and the simple moving averages lists are not reset between runs

while run < runMax:
    
    block = startingBlock
    stepTotal = 0          # number of 16 second steps to a solution

    maxSteps = 0           # the maximum steps for a solution, all blocks
    collisionCount = 0     # the number of collisions we get
    fiveXSpacingBlocks = 0 # number of blocks with >= 40 steps, 10:40
    tenXSpacingBlocks = 0  # number of blocks with >= 80 steps, 21:20
    nNetworkWeight = 0.0   # used to calculate a moving average of difficulty, for network weight
    nNetworkWeightListIndex = 0 # the index into the moving average arrays
    nStakesTime = 0.0      # used to calculate a moving average for block spacing, for network weight
    averageNewNetworkWeight = 0.0 # used to calculate average new network weight

    # if run == 0:   # print column labels
    #    print("    Block |  wallet |    weight   | true netwt | network wt |   target  | spacing")

    for i in range(numWallets): # Set new Network Weight
            walletWeight.append(int((4000000 + run * 2000000)/numWallets))

    trueNetworkWeight = 0
    for i in range(numWallets):   
        trueNetworkWeight += walletWeight[i]
  
    # block loop - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    firstInterval = 0

    while block < numBlocks + startingBlock:

        step = 1  # paramValue             # 16 second steps, 1 = start with interval 1
        firstInterval = step               # save for printing chart
        had5xSteps = False   # had 40 steps or more in this block
        had10xSteps = False  # had 80 steps or more in this block
        # target = startingTarget  # in case scaling the target below   what to do?

        # = = = = = = = = = = = = = = = = =

        if block % 100 == 0:                    # print to screen for charting
            print(block, ",", stakableWeight)

        '''
        if useDynamicWeights == True:                               # COMPLEXITY SETTING 6
            if block == 1000:    # add 20,000,000
                walletWeight[10] += 2000000
                walletWeight[11] += 2000000
                walletWeight[12] += 2000000
                walletWeight[13] += 2000000
                walletWeight[14] += 2000000
                walletWeight[15] += 2000000
                walletWeight[16] += 2000000
                walletWeight[17] += 2000000
                walletWeight[18] += 2000000
                walletWeight[19] += 2000000

                trueNetworkWeight += 20000000  # update true network weight
        '''        
        if useDynamicWeights == True:                               # COMPLEXITY SETTING 6
            if block == 1000:   
                for i in range(1375):
                    walletWeight[i] = 0;

                trueNetworkWeight = 0    

                for i in range(numWallets):   
                    trueNetworkWeight += walletWeight[i]

                print("trueNetworkWeight", trueNetworkWeight)        
        
        # step loop - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        while True:  # loop on step until we have a solution
            
            wallet = 0
            SHA256Solutions = 0

            # if step == 5:
            #     step += 1
                                                                     # COMPLEXITY SWITCH 8
            # loop through all the wallets and check for a solution and find
            # SHA-256 collisions for orphans
            # on a real blockchain all the wallets would be checking simultaneously
            
            # wallet loop - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
            
            while wallet < numWallets:  # loop through all the wallets

                # if walletStaking[wallet] == 1:   # this wallet is staking (indent below to put back)

                # get a 256 bit random number to use as the digest for SHA-256
                # use either the Python random module or the secrets module
                
                if useSecretsModule == True:                        # COMPLEXITY SWITCH 1
                    temp = str(secrets.randbits(256)).encode('utf-8')   # using secrets module
                else:
                    temp = str(random.getrandbits(256)).encode('utf-8') # using random module
                
                hash_object = hashlib.sha256(temp)    # get SHA-256 hash
                hex_dig = hash_object.hexdigest()
                                  # random module, fixed seed, first time through, 1,000 mainnet wallets
                # print(hex_dig)  # 0df34ba99348c61d540586b516925d2836103625268c6387e33f3b3a89174f9f

                hashProofOfStake = int(hex_dig, 16) # convert hex string to a really big decimal int
                # print(hashProofOfStake) # 6309933071041450796822743352002321870736073756553388285190011991562795831199
                                          # or 6.30993307104145E+75

                # = = = = = = = = = = = = = = = = = 

                if wallet == 50: # and stake > 0:  # check if any stakes have matured

                    if stakeTable[block % 500] > 0:  # found a mature stake, return it
                        stakeTable[block % 500] = 0
                        stakableWeight += stakingUTXOSize
                        walletWeight[50] = delegatedWeight + stakableWeight

                        # stake = 0
                        
                        # for i in range(500):
                        #     stake += stakeTable[i]
                        
                        # print("Return stake, block =", block, "walletWeight[50] =", walletWeight[50], "stakableWeight =", stakableWeight, "stake =", stake)

                # = = = = = = = = = = = = = = = = = 
                    
                if hashProofOfStake < target * walletWeight[wallet] * COIN:    # * step:
                    
                    SHA256Solutions += 1      # found a solution
                    walletWinner = wallet     # the block reward winner, last one in this block\

                    # = = = = = = = = = = = = = =

                    if wallet == 50:          # SuperStaker got a block reward

                        if stakableWeight > 0:

                            stakeTable[block % 500] = stakingUTXOSize
                            stakableWeight -= stakingUTXOSize
                            walletWeight[50] = delegatedWeight + stakableWeight

                            # stake = 0
                            # for i in range(500):
                            #    stake += stakeTable[i]

                            # print("Staking, block =", block, "walletWeight[50] =", walletWeight[50], "stakableWeight =", stakableWeight, "stake =", stake)

                        else:
                            print("Oops, xxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                            # winsound.Beep(400, 1000)
                            missedBlockRewards += 1

                    # = = = = = = = = = = = = = =

                    if SHA256Solutions >= 2:
                        collisionCount+= 1  # count of collisions over all blocks

                        if step < 20:
                            collisionCountByStep[step] += 1
                        else:
                            collisionCountByStep[20] += 1
                            
                        # print("Collision block", block, "wallet", wallet)
                            
                wallet += 1
                
                # end of wallet loop

            if SHA256Solutions >= 1:  # at least one solution found
       
                stepTotal += step         # total steps for all blocks

                if step > maxSteps:       # save largest step
                    maxSteps = step
                              
                if useSpacingDifficultyFile == False: # use SHA-256 results COMPLEXITY SWITCH 7

                    if useNormalDistributionForOffset == True:            # COMPLEXITY SWITCH 3
                        
                        stepOffset = random.normalvariate(offsetFromStartOfStep, standardDeviationWithinStep)
                        if stepOffset < 1.5:
                            stepOffset = 1.5   # lop off low end
                            
                        if stepOffset > 10.0:
                            stepOffset = 10.0   # lop off high end
                        
                        nActualSpacing = step * 16 + stepOffset
                        
                    else:                               # increase spacing here to reduce block time

                        nActualSpacing = step * 16   # step starts from 1

                    nTargetSpacing = nPowTargetSpacing         # pow.cpp, line 78, 128
                    
                    if nActualSpacing > nTargetSpacing * 20:   # pow.cpp, line 82, default 1280, NEW was 10
                        # print("hit limit spacing adjustment 1280 seconds")                    
                        nActualSpacing = nTargetSpacing * 20                    
                        
                else:                              # use block spacing from the file - 7777A
                    nActualSpacing = blockSpacing[block - startingBlock]

                # print("nActualSpacing", nActualSpacing)

                '''
                adjust the target (and difficulty) for the next block
                  
                
                '''

                # print("nActualSpacing before", nActualSpacing)
                # print("nActualSpacing", nActualSpacing)
                # print("nActualSpacing after", nActualSpacing)
             
                # carry offset time across blocks, 1st solution or uncles?

                
                if useRetarget == True:                                    # COMPLEXITY SWITCH 2

                    # even newer approach per Xuan Yan 2019/07/24:

                    target *= math.exp(2 * (nActualSpacing - 128) / 4000)

                    averageDifficulty += (EASIEST_DIFFICULTY / target) / numBlocks
                  
                # print(target)    

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
     
                # calculate the network weight as a moving average of difficulty divided by a
                # moving average of the total spacing for the last 72 blocks

                # convert target to difficulty, divide easiest difficulty 0x00000000ffff by target

                if useSpacingDifficultyFile == False:       # use simulation values COMPLEXITY SWITCH 7
                    dDiff = EASIEST_DIFFICULTY / target
                else:                                                  # 7777B
                    dDiff = blockDifficulty[block - startingBlock]
                                  
                # print("dDiff", dDiff)                 # 3000723.7886220054

                # subtract old moving average contribution, after initialization
                if block > nPoSInterval + startingBlock - 1:
                    # print("subtracting old...")
                    nNetworkWeight -= nNetworkWeightList[nNetworkWeightListIndex]
                    nStakesTime -= nStakesTimeList[nNetworkWeightListIndex]

                # add new value to sum, and save on list
               
                nNetworkWeight += dDiff * 4294967296
                nNetworkWeightList[nNetworkWeightListIndex] = dDiff * 4294967296
                
                # nStakesTime += nActualSpacing
                nStakesTime += nActualSpacing
                nStakesTimeList[nNetworkWeightListIndex] = nActualSpacing
                
                # get old moving average contribution value nPoSInterval blocks ago
                if nNetworkWeightListIndex == 0:
                    oldMovingAverageIndex = nPoSInterval - 1 # wrap to top of list
                else:
                    oldMovingAverageIndex = nNetworkWeightListIndex - 1

                nNetworkWeightResult = nNetworkWeight / nStakesTime  # current calculation with spacings
                newnNetworkWeightResult = nNetworkWeight / 9216    # use a fixed divisor of 9216

                nNetworkWeightResult *= STAKE_TIMESTAMP_MASK + 1       # multiply by 16
                newnNetworkWeightResult *= STAKE_TIMESTAMP_MASK + 1

                # print(newnNetworkWeightResult)
                
                averageNewNetworkWeight += newnNetworkWeightResult / COIN  # in millions

                # print("dDiff", dDiff, "nNetworkWeightListIndex", nNetworkWeightListIndex, "nNetworkWeightResult", nNetworkWeightResult, "nStakesTime", nStakesTime)
                # print(nStakesTimeList[0], nStakesTimeList[1], nStakesTimeList[2], nStakesTimeList[3], nStakesTimeList[4], nStakesTimeList[5], nStakesTimeList[6], nStakesTimeList[7], nStakesTimeList[8], nStakesTimeList[9])
                # time.sleep(0.1)
                
                nNetworkWeightListIndex += 1
                if nNetworkWeightListIndex >= nPoSInterval: # wrap
                    nNetworkWeightListIndex = 0

                if step > 20:      # just group all the bigger steps at 20
                    step = 20
                    
                stepCount[step] += 1   # count how many of each step

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -       

                break # found a SHA-256 hash solution, done with this block
            
            if step >= 40:
                had5xSteps = True # had 40 or more steps in this block

            if step >= 80:
                had10xSteps = True # had 80 or more steps in this block

            step += 1 # end of step loop
                
        if had5xSteps == True:            
            fiveXSpacingBlocks += 1
            # print("longer block, steps", step)

        if had10xSteps == True:            
            tenXSpacingBlocks += 1

        if printBlockByBlock == True:
            
            '''
            display key
            
            block is the block number

            wallet is the wallet number, like an address

            weight is the weight of the winning wallet (or the highest # wallet for a collision)

            trueNetworkWeight "true netwt" is the sum of all wallet weights. This is fixed during the simulation
            unless some dynamic changes are introduced with useDynamicWeights (commented out)
            
            target is the target for each block, no moving average

            nNetworkWeightResult is the nPoSInterval moving average of the difficulty divided by
            the nPoSInterval moving average of the block spacing, divide by COIN for display in millions
            
            spacing is the time between blocks
            
            Format the data for printing on a display. Calculate the pads to keep 
            the columns aligned. Numbers are right justified:
            
                Block |  wallet |    weight   | true netwt |   target  | network wt | spacing
                    1 |      1  |           1 |  1,234,567 |   234,567 | 12,456,789 |     3
            9,999,999 | 99,999  | 9,999,999.9 | 99,999,999 |   999,999 | 99,999,999 | 9,999
            \ pads go here                                                 
             
            '''

            if block <= 9999999:
                blockWithCommas = "{:,d}".format(int(block))
                pad = " " * (9 - len(blockWithCommas))
                blockPadCommas = pad + blockWithCommas
            else:
                blockPadCommas = "xxxxxxxxx"

            if walletWinner <= 99999:
                walletWinnerWithCommas = "{:,d}".format(int(walletWinner))
                pad = " " * (7 - len(walletWinnerWithCommas))
                walletWinnerPadCommas = pad + walletWinnerWithCommas
            else:
                walletWinnerPadCommas = "xxxxxxx"
                
            if walletWeight[walletWinner] <= 9999999:
                weightWithCommas = ("{:,f}".format(round(walletWeight[walletWinner], 1)))[:-5]
                pad = " " * (11 - len(weightWithCommas))
                weightPadCommas = pad + weightWithCommas
            else:
                weightPadCommas = "xxxxxxxxxxx"
           
            if trueNetworkWeight <= 99999999:
                trueNetworkWeightWithCommas =  "{:,d}".format(int(trueNetworkWeight))
                pad = " " * (10 - len(trueNetworkWeightWithCommas))
                trueNetworkWeightPadCommas = pad + trueNetworkWeightWithCommas
            else:
                trueNetworkWeightPadCommas = "xxxxxxxxxx"

           # target scaling factor, for printing
            printTarget = target / 10000000000000000000000000000000000000000000000000000000  # print scaling factor ???
            
            if printTarget <= 9999999:
                printTargetWithCommas = "{:,d}".format(int(printTarget))
                pad = " " * (9 - len(printTargetWithCommas))
                printTargetPadCommas = pad + printTargetWithCommas
            else:
                printTargetPadCommas = "xxxxxxxxx"
                
            if (block >= nPoSInterval + startingBlock):   # nNetworkWeight or "Network Weight"
                                          # is a simple moving average for nPoSInterval
                                          # blocks of the reciprocal of the target divided by
                                          # the block spacing for nPosInterval blocks

                nNetworkWeightResultMillions = nNetworkWeightResult / COIN              
                if nNetworkWeightResultMillions <= 99999999:
                    nNetworkWeightResultMillionsWithCommas =  "{:,d}".format(int(nNetworkWeightResultMillions))
                    pad = " " * (10 - len(nNetworkWeightResultMillionsWithCommas))
                    nNetworkWeightResultMillionsPadCommas = pad + nNetworkWeightResultMillionsWithCommas
                else:
                    nNetworkWeightResultMillionsPadCommas = "xxxxxxxxxx"
                    
            else:
                nNetworkWeightResultMillionsPadCommas = "   not yet"  # no pseudoNetworkWeight for the first nPoSInterval blocks  

            if (block >= nPoSInterval + startingBlock):   

                newnNetworkWeightResultMillions = newnNetworkWeightResult / COIN              
                if newnNetworkWeightResultMillions <= 99999999:
                    newnNetworkWeightResultMillionsWithCommas =  "{:,d}".format(int(newnNetworkWeightResultMillions))
                    pad = " " * (10 - len(newnNetworkWeightResultMillionsWithCommas))
                    newnNetworkWeightResultMillionsPadCommas = pad + newnNetworkWeightResultMillionsWithCommas
                else:
                    newnNetworkWeightResultMillionsPadCommas = "xxxxxxxxxx"
                    
            else:
                newnNetworkWeightResultMillionsPadCommas = "   not yet"  # no pseudoNewNetworkWeight for the first nPoSInterval blocks  
       
            if nActualSpacing <= 9999:
                nActualSpacingWithCommas = ("{:,f}".format(round(nActualSpacing, 1)))[:-7]
                pad = " " * (7 - len(nActualSpacingWithCommas))
                nActualSpacingPadCommas = pad + nActualSpacingWithCommas
            else:
                nActualSpacingPadCommas = "xxxxx"
                
            # if run == 0:   # print column labels
            #     print("    Block |  wallet |    weight   | true netwt | network wt |   target  | spacing")

            print(blockPadCommas, "|", walletWinnerPadCommas, "|", weightPadCommas, "|", trueNetworkWeightPadCommas, "|", nNetworkWeightResultMillionsPadCommas, "|", newnNetworkWeightResultMillionsPadCommas, "|", printTargetPadCommas, "|", nActualSpacingPadCommas)

        if logBlockByBlock == True:

            '''
            sample in Excel

                Block |  wallet |    weight   | true netwt | network wt |  target | spacing
                    1 |      1  |           1 |  1,234,567 |  1,234,567 |  12,456 |     3
            9,999,999 | 99,999  | 9,999,999.9 | 99,999,999 | 99,999,999 | 999,999 | 9,999
            
            block      wallet   weight    target        net weight    spacing
            8473	577	9248	15.88376106	133.4529068
            8474	84	20941	15.89595998	180.6929067
            8475	1	892220	15.9042698	212.8724866
            '''
            
            logTarget = target / 10000000000000000000000000000000000000000000000000000000  # scaling factor for 16 m network weight in logging

            if block >= nPoSInterval + startingBlock:
                nNetworkWeightResultMillions = nNetworkWeightResult / COIN
                newnNetworkWeightResultMillions = newnNetworkWeightResult / COIN  # with a fixed divisor
                tempStr = str(block) + "," + str(walletWinner) + "," + str(trueNetworkWeight) + "," + str(nNetworkWeightResultMillions) + "," + str(newnNetworkWeightResultMillions) + "," + str(logTarget) + "," + str(nActualSpacing) + "," + str(dDiff)

            else:  # no good values yet for the true wallet and network weight averages
                tempStr = str(block) + "," + str(walletWinner) + "," + str(trueNetworkWeight) + "," + "not yet,not yet," + str(logTarget) + "," + str(nActualSpacing) + "," + str(dDiff)
             
            outFileQSBES.write(tempStr)
            outFileQSBES.write('\n')
            # time.sleep(0.01)

        block += 1  # end of block loop

    '''
    Format the data for printing on a display. Calculate the pads to keep 
    the columns aligned. Numbers are right justified:
        
            Run |  paramValue | ave secs | >=640 blks | >=1280 blks | max secs |   collisns |  ave nt wt
              1 |           1 |   128.00 |          0 |           0 |        0 |          0 |     0.00
            999 | 999,999,999 | 9,999.00 |    999,999 |     999,999 |  999,999 |    999,999 |    99.99
           \ pads go here

    '''

    if run <= 999:
        runWithCommas = "{:,d}".format(run)
        pad = " " * (5 - len(runWithCommas))
        runPadCommas = pad + runWithCommas
    else:
        runPadCommas = "xxx"

    # parameter value - float

    # True Network Weight to print

    paramValue2 = trueNetworkWeight / 1000000  # in millions
    
    if paramValue2 <= 999999.999:
        paramValueWithCommas = "{:,f}".format(paramValue)[:-3]  #  xx.xxx
        pad = " " * (11 - len(paramValueWithCommas))
        paramValuePadCommas = pad + paramValueWithCommas
    else:
        paramValuePadCommas = "xxxxxxxxxxx"

    aveSeconds = 16 * float(stepTotal) / numBlocks # is there a better value?
    
    if aveSeconds <= 9999.99:
        aveSecondsWithCommas = ("{:,f}".format(aveSeconds))[:-4]  # xx.xx
        pad = " " * (8 - len(aveSecondsWithCommas))
        aveSecondsPadCommas = pad + aveSecondsWithCommas
    else:
        aveSecondsPadCommas = "xxxxxxxx"
   
    if fiveXSpacingBlocks <= 999999:
        fiveXSpacingBlocksWithCommas =  "{:,d}".format(int(fiveXSpacingBlocks))
        pad = " " * (10 - len(fiveXSpacingBlocksWithCommas))
        fiveXSpacingBlocksPadCommas = pad + fiveXSpacingBlocksWithCommas
    else:
        fiveXSpacingBlocksPadCommas = "  xxxxxxxx"

    if tenXSpacingBlocks <= 999999:
        tenXSpacingBlocksWithCommas =  "{:,d}".format(int(tenXSpacingBlocks))
        pad = " " * (11 - len(tenXSpacingBlocksWithCommas))
        tenXSpacingBlocksPadCommas = pad + tenXSpacingBlocksWithCommas
    else:
        tenXSpacingBlocksPadCommas = "   xxxxxxxx"

    maxSeconds = maxSteps * 16 # is there a better number?
    
    if maxSeconds <= 999999:
        maxSecondsWithCommas = "{:,d}".format(int(maxSeconds))
        pad = " " * (8 - len(maxSecondsWithCommas))
        maxSecondsPadCommas = pad + maxSecondsWithCommas
    else:
        maxSecondsPadCommas = "xxxxxxxx"
    
    if collisionCount <= 9999999:
        collisionsPercent = 100 * collisionCount / numBlocks
        collisionsPercentWithCommas = "{:,f}".format(collisionsPercent)[:-4]
        pad = " " * (10 - len(collisionsPercentWithCommas))
        collisionsPercentPadCommas = pad + collisionsPercentWithCommas
    else:
        collisionsPercentPadCommas = " xxxxxxxxx"

    averageNewNetworkWeight /= (numBlocks + startingBlock)                 # compute average
    averageNewNetworkWeight = round(averageNewNetworkWeight / 1000000, 2)  # in millions

    # print(averageNewNetworkWeight)

    if averageNewNetworkWeight <= 99.99:
        averageNewNetworkWeightCommas = ("{:,f}".format(averageNewNetworkWeight))[:-4]  # xx.xx
        pad = " " * (10 - len(averageNewNetworkWeightCommas))
        averageNewNetworkWeightPadCommas = pad + averageNewNetworkWeightCommas
    else:
        averageNewNetworkWeightPadCommas = "xxxxx"    

    if run == 0: # print column labels

        # brute force centering for the parameter name
        
        lenStr = len(paramLabel)

        if lenStr >= 11:
            printStr =  " " + paramLabel[:11] + " " # chop first 11 characters
        elif lenStr == 10:
            printStr = "  " + paramLabel + " "
        elif lenStr == 9:
            printStr = "  " + paramLabel + "  "
        elif lenStr == 8:
            printStr = "   " + paramLabel + "  "
        elif lenStr == 7:
            printStr = "   " + paramLabel + "   "
        elif lenStr == 6:
            printStr = "    " + paramLabel + "   "
        elif lenStr == 5:
            printStr = "    " + paramLabel + "    "
        elif lenStr == 4:
            printStr = "     " + paramLabel + "    "
        elif lenStr == 3:
            printStr = "     " + paramLabel + "     "
        elif lenStr == 2:
            printStr = "      " + paramLabel + "     "
        else: # len == 1
            printStr = "      " + paramLabel + "      "

        tempStr = "  Run |" + printStr + "| ave secs | >=640 blks | >=1280 blks | max secs |   collisns | ave net wt | ave difficulty"
        print(tempStr)
        
    print("Missed block rewards =", missedBlockRewards)
             
    print(runPadCommas, "|", paramValuePadCommas, "|", aveSecondsPadCommas, "|", fiveXSpacingBlocksPadCommas, "|", tenXSpacingBlocksPadCommas, "|", maxSecondsPadCommas, "|", collisionsPercentPadCommas, "|", averageNewNetworkWeightPadCommas, "|", averageDifficulty)

    if enableLogging == True:

        if run == 0:  # write column labels to log
            tempStr = "Run," + printStr + ",ave secs,>=640 blks,>=1280 blks, max secs,collisions"  # little kludgy with printStr
            outFileQSBES.write(tempStr)
            outFileQSBES.write('\n')
            time.sleep(0.01)               
            
        tempStr = str(run + 1) + "," + str(paramValue) + "," + str(aveSeconds) + "," + str(fiveXSpacingBlocks) + "," + str(tenXSpacingBlocks) + "," + str(maxSeconds) + "," + str(collisionCount)

        outFileQSBES.write(tempStr)
        outFileQSBES.write('\n')
        time.sleep(0.01)
  
    # increment the parameter here, some examples

    # targetScalingFactor += paramIncrement  # for incrementing target scaling factor
    # paramValue = targetScalingFactor

    # startingStep += paramIncrement           # for stepping by 2 the startingStep value
    # paramValue = startingStep

    run += 1
    
    if run < runMax:
        paramValue += 1    # load the next min step

    # end of param loop    

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# format chart, default chart:

rowMax = 22
columnMax = 55  # reset below based on required chart height
row = 0
column = 0

# rotatedRowMax = columnMax
# rotatedColumnMax = columnMax
# rotatedRow = 0
# rotatedColumn = 0
 
arr = [[0 for i in range(columnMax)] for j in range(rowMax)] 

overrun = False
barMax = 0          
        
for i in range(1,21):

    bar = int(round(2.5 * 100 * stepCount[i] / numBlocks))  # double percent for bar graph

    if bar > barMax:
        barMax = bar           # save the maximum bar length

    if bar > columnMax - 1:
        bar = columnMax - 1
        overrun = True

    tempStr = ""

    while bar > 0:
        tempStr += "#"
        arr[i - 1][bar] = 1
        bar -= 1

    if i <= 9:
        formattedI = " " + str(i)
    else:
        formattedI = str(i)

    percent = 100 * stepCount[i] / numBlocks

    if percent < 10:
        spacer = " "
    else:
        spacer = ""

    tempStr2 = formattedI + spacer

    
    # uncomment this next line to print a horizontal chart:
    # print("interval", tempStr2, "{:,f}".format(100 * stepCount[i] / numBlocks)[:-5], tempStr)

# print("barMax =", barMax)

# adjust chart height based on maximum bar size

if barMax > 30:
    columnMax = barMax + 3    # taller chart
else:
    columnMax = 30            # normal height chart, up to XX percent
    

if overrun == True:
    graphChars = "OVR"   # signal we ran over
else:
    graphChars = "###"

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

print("")


collisionPcts = "Collisns "

for i in range(1, 21):
    collisionPcts += str("{:.2f}".format(round((100 * collisionCountByStep[i] / numBlocks), 2)))
    collisionPcts += " "
     
# print(collisionPcts)

# print sum percent of intervals 6 through 10

tmpSum = 0
          
for i in range(6,11):         # get the precent sum for intervals 6 - 10
    tmpSum += stepCount[i]
    
# print("Interval 6 - 10 percent", "{:,f}".format(100 * tmpSum / numBlocks)[:-5])
tempStr = "5 x spacings: " + str(fiveXSpacingBlocks) +", 10 x spacings: " + str(tenXSpacingBlocks) + ", collisions %: " + str(collisionsPercent) 
print(tempStr)

print("delegatedWeight =", delegatedWeight, "staking UTXOs number =", numberOfStakingUTXOs, "staking UTXO size =", stakingUTXOSize)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
      
end = timer()
print("Simulation duration in seconds:", format(end - start, "0.2f"))
# print("ending target", target, "ending difficulty", dDiff, "average Difficulty", averageDifficulty)
# print("true network weight", trueNetworkWeight)

if enableLogging == True:
    outFileQSBES.close()

# winsound.Beep(1000, 500)


    

