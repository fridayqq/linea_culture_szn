from web3 import Web3
import time, random, requests, json
from decimal import Decimal
from loguru import logger
from tqdm import tqdm
from sys import stderr
from random import (
    randint,
    uniform,
)

############################## Config #################################################

time_delay_min = 600  # Min delay between accs in seconds
time_delay_max = 2400  # Max delay between accs in seconds

# Прокси настройки
proxy_file = "proxies.txt"  # Файл со списком прокси
private_keys = "private_keys.txt"  # Файл со списком приватных ключей

#######################################################################################

logger.remove()
logger.add(stderr, format="<lm>{time:YYYY-MM-DD HH:mm:ss}</lm> | <level>{level: <8}</level>| <lw>{message}</lw>")

def create_web3_instance(proxy):
    session = requests.Session()
    session.proxies = {"http": proxy, "https": proxy}
    return Web3(Web3.HTTPProvider('https://linea.blockpi.network/v1/rpc/public', 
                                  session=session,
                                  request_kwargs={'timeout': 30}))

def add_gas_limit(tx, web3):
    try:
        tx['gas'] = web3.eth.estimate_gas(tx)
    except:
        tx['gas'] = random.randint(220000, 250000)
    return tx

def mintNFT(private_key, address_wallet, data, toContract, quest, web3):
    txData = {
        'from': address_wallet,
        'to': Web3.to_checksum_address(toContract),
        'nonce': web3.eth.get_transaction_count(address_wallet),
        'gasPrice': int(web3.eth.gas_price * uniform(1.01, 1.02)),
        'value': 0,
        'gas': 0,
        'data': data
        }    
    add_gas_limit(txData, web3)
    signed_tx = web3.eth.account.sign_transaction(txData, private_key)
    
    try:
        raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash = web3.to_hex(raw_tx_hash)
        tx_receipt = web3.eth.wait_for_transaction_receipt(raw_tx_hash, timeout=600)
        status = tx_receipt.status
        if status == 1:
            logger.success(f'Minted {quest} NFT https://lineascan.build/tx/{tx_hash}')
            return True
        else:
            if getTxStatus(tx_hash, web3): 
                logger.success(f'Minted {quest} NFT https://lineascan.build/tx/{tx_hash}')
                return True
            else:
                logger.error(f'Mint {quest} NFT failed. TX status = {status}')
                return False
    except Exception as e:
        logger.error(f'Mint {quest} NFT failed: {e}')
        return False
        
def getTxStatus(tx_hash, web3):
    time.sleep(30)
    tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
    status = tx_receipt.status
    returnStatus = True if status == 1 else False
    return returnStatus

def main():
    logger.info('This script will mint W2: Toad the Great')
    logger.info('https://app.layer3.xyz/quests/w2-toad?slug=w2-toad')
    with open(private_keys, "r") as f:
        keys_list = [row.strip() for row in f]
    
    with open(proxy_file, "r") as f:
        proxies_list = [row.strip() for row in f]
    
    if len(keys_list) != len(proxies_list):
        logger.error("The number of private keys does not match the number of proxies.")
        return

    wallet_proxy_pairs = list(zip(keys_list, proxies_list))
    random.shuffle(wallet_proxy_pairs)
    
    count_wallets = len(wallet_proxy_pairs)
    number_wallets = 0

    for key, proxy in wallet_proxy_pairs:
        number_wallets += 1
        web3 = create_web3_instance(proxy)
        address_wallet = web3.eth.account.from_key(key).address
        logger.info(f'{number_wallets}/{count_wallets} - {address_wallet} (Proxy: {proxy})')
        mintNFT(key, address_wallet, '0x00000000', '0x0841479e87Ed8cC7374d3E49fF677f0e62f91fa1', 'W2: Toad the Great', web3)
        time.sleep(15)
            
        sleepDelay = random.randint(time_delay_min, time_delay_max)
        for i in tqdm(range(sleepDelay), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
            time.sleep(1)
        print()
    logger.info('Done! Теперь иди прокликивай!')

main()