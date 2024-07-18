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

time_delay_min = 60  # Min delay between accs in seconds
time_delay_max = 2400  # Max delay between accs in seconds

# Прокси настройки
proxy_file = "proxies.txt"  # Файл со списком прокси
private_keys = "private_keys.txt"  # Файл со списком приватных ключей

#######################################################################################

logger.remove()
logger.add(stderr, format="<lm>{time:YYYY-MM-DD HH:mm:ss}</lm> | <level>{level: <8}</level>| <lw>{message}</lw>")

quest_name = "W3: Danielle Zosavac"
quest_link = "https://app.layer3.xyz/quests/w3-danielle-zosavac?slug=w3-danielle-zosavac"
contract = "0x3A21e152aC78f3055aA6b23693FB842dEFdE0213"
method_id = "0x00000000"


TRANSACTION_ATTRIBUTE = None


def determine_transaction_attribute():
    global TRANSACTION_ATTRIBUTE
    # Создаем тестовую транзакцию
    web3 = Web3(Web3.HTTPProvider('https://linea.blockpi.network/v1/rpc/public'))
    account = web3.eth.account.create()
    tx_data = {
        'nonce': 0,
        'gasPrice': 20000000000,
        'gas': 21000,
        'to': account.address,
        'value': 1,
        'data': b'',
    }
    signed_tx = account.sign_transaction(tx_data)
    
    if hasattr(signed_tx, 'rawTransaction'):
        TRANSACTION_ATTRIBUTE = 'rawTransaction'
    elif hasattr(signed_tx, 'raw_transaction'):
        TRANSACTION_ATTRIBUTE = 'raw_transaction'
    else:
        raise AttributeError("Unable to find valid transaction attribute")

    logger.info(f"Using '{TRANSACTION_ATTRIBUTE}' as the transaction attribute")


determine_transaction_attribute()


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


def mint_nft(private_key, address_wallet, web3):
    tx_data = {
        'from': address_wallet,
        'to': Web3.to_checksum_address(contract),
        'nonce': web3.eth.get_transaction_count(address_wallet),
        'gasPrice': int(web3.eth.gas_price * uniform(1.01, 1.02)),
        'value': 0,
        'gas': 0,
        'data': method_id
    }    
    add_gas_limit(tx_data, web3)
    signed_tx = web3.eth.account.sign_transaction(tx_data, private_key)
    
    try:
        raw_tx_hash = web3.eth.send_raw_transaction(getattr(signed_tx, TRANSACTION_ATTRIBUTE))
        tx_hash = web3.to_hex(raw_tx_hash)
        tx_receipt = web3.eth.wait_for_transaction_receipt(raw_tx_hash, timeout=600)
        status = tx_receipt.status 
        if status == 1:
            logger.success(f'Minted NFT https://lineascan.build/tx/{tx_hash}')
            return True
        else:
            if get_tx_status(tx_hash, web3): 
                logger.success(f'Minted NFT https://lineascan.build/tx/{tx_hash}')
                return True
            else:
                logger.error(f'Mint NFT failed. TX status = {status}')
                return False
    except Exception as e:
        logger.error(f'Mint NFT failed: {e}')
        return False


def get_tx_status(tx_hash, web3):
    time.sleep(30)
    tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
    status = tx_receipt.status
    return_status = True if status == 1 else False
    return return_status


def main():
    logger.info(f'This script will mint {quest_name}')
    logger.info(f'{quest_link}')
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
        mint_nft(key, address_wallet, web3)
        time.sleep(15)
            
        sleep_delay = random.randint(time_delay_min, time_delay_max)
        for _ in tqdm(range(sleep_delay), desc=f'Sleeping for {sleep_delay} seconds', ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}'):
            time.sleep(1)
        print()
    logger.info('Done! Теперь иди прокликивай!')


main()
