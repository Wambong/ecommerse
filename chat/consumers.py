import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
import base64


from chat.models import Thread, ChatMessage

User = get_user_model()


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print('connected', event)
        user = self.scope['user']
        chat_room = f'user_chatroom_{user.id}'
        self.chat_room = chat_room
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        await self.send({
            'type': 'websocket.accept'
        })


    async def websocket_receive(self, event):
        print('receive', event)
        received_data = json.loads(event['text'])
        msg = received_data.get('message')
        media_data = received_data.get('media')
        sent_by_id = received_data.get('sent_by')
        send_to_id = received_data.get('send_to')
        thread_id = received_data.get('thread_id')

        sent_by_user = await self.get_user_object(sent_by_id)
        send_to_user = await self.get_user_object(send_to_id)
        thread_obj = await self.get_thread(thread_id)

        if not sent_by_user:
            print('Error: Sent by user is incorrect')
            return

        if not send_to_user:
            print('Error: Send to user is incorrect')
            return

        if not thread_obj:
            print('Error: Thread id is incorrect')
            return

        if msg or media_data:
            # Handle text message or media file upload
            media_file = None
            if media_data:
                # Handle media file upload
                media_file = self.decode_base64_and_save(media_data)

            await self.create_chat_message(thread_obj, sent_by_user, msg=msg, media=media_file)

        other_user_chat_room = f'user_chatroom_{send_to_id}'
        self_user = self.scope['user']
        response = {
            'message': msg,
            'sent_by': self_user.id,
            'thread_id': thread_id
        }

        await self.channel_layer.group_send(
            other_user_chat_room,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            }
        )

        await self.channel_layer.group_send(
            self.chat_room,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            }
        )


    async def websocket_disconnect(self, event):
        print('disconnect', event)

    async def chat_message(self, event):
        print('chat_message', event)
        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        })

    @database_sync_to_async
    def get_user_object(self, user_id):
        qs = User.objects.filter(id=user_id)
        if qs.exists():
            obj = qs.first()
        else:
            obj = None
        return obj

    @database_sync_to_async
    def get_thread(self, thread_id):
        qs = Thread.objects.filter(id=thread_id)
        if qs.exists():
            obj = qs.first()
        else:
            obj = None
        return obj

    @database_sync_to_async
    def create_chat_message(self, thread, user, msg=None, media=None):
        if msg or media:
            return ChatMessage.objects.create(thread=thread, user=user, message=msg, media=media)
        return None


    def decode_base64_and_save(self, media_data):
        try:
            format, imgstr = media_data.split(';base64,')
            ext = format.split('/')[-1]
            media_file = ContentFile(base64.b64decode(imgstr), name=f'uploaded_media.{ext}')
            return media_file
        except Exception as e:
            print('Error decoding and saving media:', e)
            return None
