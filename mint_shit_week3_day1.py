from web3 import Web3
import time, random, requests, json
from decimal import Decimal
from loguru import logger
from tqdm import tqdm
from sys import stderr
from random import uniform
import eth_abi

############################## Config #################################################

time_delay_min = 600  # Min delay between accs in seconds
time_delay_max = 2400  # Max delay between accs in seconds

# Персональные настройки
proxy_file = "proxies.txt"  # Файл со списком прокси
private_keys = "private_keys.txt"  # Файл со списком приватных ключей

#######################################################################################

logger.remove()
logger.add(stderr, format="<lm>{time:YYYY-MM-DD HH:mm:ss}</lm> | <level>{level: <8}</level>| <lw>{message}</lw>")

quest_name = "W3: AscendTheEnd"
quest_link = "https://app.layer3.xyz/quests/w3-ascendtheend-1?slug=w3-ascendtheend-1"


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


def launchpad_buy(private_key, address_wallet, to_contract, web3):
    method_id = '0x1b7af8fc'
    selector = '0x0c21cfbb'
    launchpad_id = '0x19a747c1'
    slot_id = 0
    quantity = 1
    additional = []
    data = '0x'

    # Manually encode each parameter
    encoded_selector = selector.replace('0x', '') + '0' * 56  # Правильное заполнение для bytes4
    encoded_launchpad_id = launchpad_id.replace('0x', '') + '0' * 56  # Правильное заполнение для bytes4
    encoded_slot_id = hex(slot_id)[2:].zfill(64)
    encoded_quantity = hex(quantity)[2:].zfill(64)
    
    # Encode additional array offset
    encoded_additional_offset = hex(32 * 6)[2:].zfill(64)  # Offset to the start of the additional array
    
    # Encode data offset
    encoded_data_offset = hex(32 * 7)[2:].zfill(64)  # Offset to the start of the data
    
    # Encode additional array
    encoded_additional_length = hex(len(additional))[2:].zfill(64)
    
    # Encode data
    encoded_data_length = hex(0)[2:].zfill(64)  # Length of the data (empty)

    encoded_all = (
        method_id +
        encoded_selector +
        encoded_launchpad_id +
        encoded_slot_id +
        encoded_quantity +
        encoded_additional_offset +
        encoded_data_offset +
        encoded_additional_length +
        encoded_data_length
    )

    tx_data = {
        'from': address_wallet,
        'to': Web3.to_checksum_address(to_contract),
        'nonce': web3.eth.get_transaction_count(address_wallet),
        'gasPrice': int(web3.eth.gas_price * uniform(1.01, 1.02)),
        'value': 0,  # Set to 0 or the required amount if the function is payable
        'gas': 0,
        'data': encoded_all
    }    
    add_gas_limit(tx_data, web3)
    signed_tx = web3.eth.account.sign_transaction(tx_data, private_key)
    
    try:
        raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash = web3.to_hex(raw_tx_hash)
        tx_receipt = web3.eth.wait_for_transaction_receipt(raw_tx_hash, timeout=600)
        status = tx_receipt.status
        if status == 1:
            logger.success(f'Launchpad buy successful https://lineascan.build/tx/{tx_hash}')
            return True
        else:
            if get_tx_status(tx_hash, web3): 
                logger.success(f'Launchpad buy successful https://lineascan.build/tx/{tx_hash}')
                return True
            else:
                logger.error(f'Launchpad buy failed. TX status = {status}')
                return False
    except Exception as e:
        logger.error(f'Launchpad buy failed: {e}')
        return False
    

def get_tx_status(tx_hash, web3):
    time.sleep(30)
    tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
    status = tx_receipt.status
    return_status = True if status == 1 else False
    return return_status


def main():
    logger.info(f'This script will perform launchpad buy for {quest_name}')
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
        launchpad_buy(key, address_wallet, '0xBcFa22a36E555c507092FF16c1af4cB74B8514C8', web3)
        time.sleep(15)
            
        sleep_delay = random.randint(time_delay_min, time_delay_max)
        for i in tqdm(range(sleep_delay), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
            time.sleep(1)
        print()
    logger.info('Done! Теперь иди прокликивай!')

main()