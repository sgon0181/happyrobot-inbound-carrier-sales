"""Codes go only to the configured demo inbox, never a caller-supplied address."""
import asyncio
from email.message import EmailMessage
import smtplib
import ssl


class EmailNotifier:
    def __init__(self,values,platform):self.values,self.platform=values,platform
    async def __call__(self,code,run_id):
        if self.values.get('OTP_EMAIL_CREDENTIAL'):
            def send():
                user=self.values.get('OTP_EMAIL_USER') or self.values['DEMO_OTP_EMAIL']
                message=EmailMessage();message['From']=user;message['To']=self.values['DEMO_OTP_EMAIL']
                message['Subject']='Carrier Sales Prototype verification code'
                message.set_content('Your demo verification code is '+code+'. It expires in five minutes.')
                with smtplib.SMTP_SSL('smtp.gmail.com',465,timeout=5,context=ssl.create_default_context()) as server:
                    server.login(user,self.values['OTP_EMAIL_CREDENTIAL']);server.send_message(message)
                return {'sent':True,'source':'LIVE_SMTP'}
            return await asyncio.to_thread(send)
        # Temporary tested route. Expected codes enter privileged notification
        # action logs, but never the voice run or the conversational agent.
        p=self.platform
        async with p.notification_lock:
            base='/versions/01a18ffa-eec2-7491-a0fe-f3ac8333d60e/nodes/'
            fixture=base+'01a18ffb-8428-734f-b6f6-a0d3ca72efa0/custom-output'
            await asyncio.to_thread(p.request,fixture,{'data':{'otp':code,'run_id':run_id}},'PUT')
            try:
                result=await asyncio.to_thread(p.request,base+'01a18ffb-8432-7ba0-96d8-0ed8c2a1944a/test',
                                               {'environment':'development'})
                output=result.get('data',{});data=output.get('data') or {}
                status=data.get('status',data.get('status_code',data.get('statusCode')))
                return {'sent':status in (200,202) and not output.get('error'),
                        'submitted':bool(output.get('id')) and not output.get('error'),
                        'source':'LIVE_NATIVE_NODE_TEST_TEMPORARY','message_id':output.get('id')}
            finally:
                await asyncio.to_thread(p.request,fixture,
                    {'data':{'otp':'SCHEMA_ONLY_NOT_A_VALID_CODE','run_id':'SCHEMA_ONLY_NOT_A_REAL_CALL'}},'PUT')
