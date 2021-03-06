import sys
import os
import pytest
import pyethereum.indexdb
import pyethereum.utils
import pyethereum.db
from tests.utils import set_db
import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger()


def act(num):
    return pyethereum.utils.sha3(str(num)).encode('hex')[:40]


def mktx(a, b):
    return 'tx(%d,%d)' % (a, b)

@pytest.fixture(scope="module")
def idx():
    set_db()
    return pyethereum.indexdb.AccountTxIndex(i_know_what_im_doing=True)


def test_appending():
    set_db()
    idx = pyethereum.indexdb.Index('namespace', i_know_what_im_doing=True)
    key = 'key'
    vals = ['v0', 'v1']
    for v in vals:
        idx.append(key, v)
    assert idx.num_values(key) == 2
    assert list(idx.get(key)) == vals

@pytest.mark.xfail # db deleting broken
def test_adding(idx):
    acct = act(10000)
    acct2 = act(10000)
    tx0 = mktx(0, 0)
    tx1 = mktx(0, 1)
    tx2 = mktx(0, 2)
    tx3 = mktx(0, 3)

    idx.add_transaction(acct, 0, tx0)
    idx.db.commit()
    txs = list(idx.get_transactions(acct, offset=0))
    assert txs == [tx0]

    idx.add_transaction(acct2, 0, tx0)
    idx.db.commit()
    txs = list(idx.get_transactions(acct2, offset=0))
    assert txs == [tx0]

    idx.add_transaction(acct, 1, tx1)
    idx.db.commit()
    txs = list(idx.get_transactions(acct, offset=0))
    assert txs == [tx0, tx1]

    idx.add_transaction(acct, 2, tx2)
    idx.db.commit()
    txs = list(idx.get_transactions(acct, offset=0))
    assert txs == [tx0, tx1, tx2]

    idx.add_transaction(acct, 3, tx3)
    idx.db.commit()
    txs = list(idx.get_transactions(acct, offset=0))
    assert txs == [tx0, tx1, tx2, tx3]

    txs = list(idx.get_transactions(acct, offset=2))
    assert txs == [tx2, tx3]

    # delete transaction
    for keep in reversed(range(4)):
        idx.delete_transactions(acct, offset=keep)
        idx.db.commit()
        txs = list(idx.get_transactions(acct, offset=0))
        assert txs == [tx0, tx1, tx2, tx3][:keep]


@pytest.mark.xfail # db deleting broken
def test_multiple_accounts(idx):
    NUM_ACCOUNTS = 20

    for i in range(NUM_ACCOUNTS)[1:]:
        acct = act(i)
        for j in range(i * 5):
            idx.add_transaction(acct, j, mktx(i, j))
        idx.db.commit()
        txs = list(idx.get_transactions(acct, offset=0))
        assert len(txs) == j + 1
        for j in range(i * 5):
            tx = mktx(i, j)
            assert tx == txs[j]
        for j in range(i * 5):
            tx = mktx(i, j)
            txs = list(idx.get_transactions(acct, offset=j))
            assert tx == txs[0]

    assert len(
        set(list(idx.get_accounts(account_from='')))) == NUM_ACCOUNTS - 1

@pytest.mark.xfail # db deleting broken
def test_num_transactions(idx):
    acct = act(4200000)
    assert idx.num_transactions(acct) == 0

    for j in range(50):
        idx.add_transaction(acct, j, mktx(j, j))
        assert idx.num_transactions(acct) == j + 1

    idx.delete_transactions(acct, offset=5)
    assert idx.num_transactions(acct) == 5
