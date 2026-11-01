"""SIMULATED native API transport. No external network or booking."""
import unittest
from service.adapters.confirmation import NativeConfirmation


def message(identity,role,text,at,session='s1'):
    return {'id':identity,'role':role,'content':text,'timestamp':at,'session_id':session}


class PlatformFixture:
    def __init__(self,pages):self.pages,self.paths=pages,[]
    def request(self,path):
        self.paths.append(path)
        if path=='/runs/c1':return {'workflow_id':'w1'}
        if path=='/runs/c1/sessions':return {'data':[{'id':sid} for sid in self.pages]}
        for sid,pages in self.pages.items():
            prefix='/sessions/'+sid+'/messages?page='
            if path.startswith(prefix):
                page=int(path[len(prefix):]);return {'data':pages[page-1],
                    'pagination':{'has_next_page':page<len(pages)}}
        raise AssertionError('Unexpected fixture request')


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_numbered_pages_and_trusted_timestamp_order(self):
        p=PlatformFixture({'s1':[[message('q','assistant','May I book load LD1 at $1075 total?',2),
                                 message('anchor','user','1075 please',1)],
                                [message('yes','user','Yes please',3)]]})
        result=await NativeConfirmation(p,'w1')('c1','LD1',1075,'anchor')
        self.assertTrue(result['approved']);self.assertEqual(result['session_id'],'s1')
        self.assertIn('/sessions/s1/messages?page=2',p.paths)

    async def test_answer_in_another_session_cannot_authorize(self):
        p=PlatformFixture({'s1':[[message('anchor','user','1075 please',1),
                                 message('q','assistant','May I book load LD1 at $1075 total?',2)]],
                           's2':[[message('yes','user','Yes please',3,'s2')]]})
        result=await NativeConfirmation(p,'w1')('c1','LD1',1075,'anchor')
        self.assertFalse(result['approved'])

    async def test_wrong_session_page_is_rejected(self):
        p=PlatformFixture({'s1':[[message('yes','user','Yes',3,'different')]]})
        with self.assertRaises(ValueError):await NativeConfirmation(p,'w1')('c1','LD1',1075,'anchor')

    async def test_missing_page_data_is_not_a_complete_transcript(self):
        p=PlatformFixture({'s1':[[]]});original=p.request
        def broken(path):return {} if '/messages?' in path else original(path)
        p.request=broken
        with self.assertRaises(ValueError):await NativeConfirmation(p,'w1')('c1','LD1',1075,'anchor')
