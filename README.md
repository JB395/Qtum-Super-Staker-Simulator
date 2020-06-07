# Qtum-Super-Staker-Simulator

Simulate Wallet Weight for Super Staker

A program to simulate blockchain operations to analyze wallet weight (# of staking UTXOs used) for a Super Staker.

Here the Super Staker is wallet[50], and has its Wallet Weight debited for stakes and credited when stakes are returned.

This program is used to determine the number of UTXOs needed for various sizes of Delegate Weight.

## Primary parameters

```
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
```

## Program Summary

set switches & parameters for simulation complexity

if doing replay, read file for spacing and difficulty

initialize log file

set starting target, based on network weight and number of wallets

load the wallets: uniform, random, simulated mainnet

 ```   parameter loop - - - - - - - - - - - - - - - - - - - - - -
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
   ```

## Typical Output

```Qtum Super Staker Simulator, version 2020-06-07
enableLogging = False, printBlockByBlock = False, logBlockByBlock = False
Using Python secrets module for cryptographically strong random numbers
useRetarget = True, retarget on every block
useNormalDistributionForOffset = False, use fixed block times at the start of the 16 second steps
Loading wallets with Mainnet distribution
useDynamicWeights = False, wallet weights are fixed during the simulation run
Starting Sun 07 Jun 2020 20:39:02 GMT
delegatedWeight = 105000 staking UTXOs number = 10 staking UTXO size = 150 staking UTXO weight = 1500
walletWeight[50] = 106500
trueNetworkWeight 20078817
Wallets 1000 blocks 60750 startingBlock 0 runs 1
Running simulation - - - - - - - - - - - - - - - - - - - - - - - -
block, wallet weight
0 , 1500
100 , 1500
200 , 1500
300 , 1350
400 , 1200
500 , 1200
600 , 900
700 , 750
800 , 900
900 , 1050
1000 , 1050
1100 , 1350
1200 , 1350
1300 , 1350
1400 , 1350
<snip>
```

### Output if Wallet Weight is zero when wallet[50] wins a block reward

```3300 , 300
3400 , 150
3500 , 150
3600 , 300
3700 , 0
Oops, xxxxxxxxxxxxxxxxxxxxxxxxxxxx
3800 , 0
3900 , 150
4000 , 150
4100 , 150
```
