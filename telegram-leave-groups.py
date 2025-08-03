"""
Script para salir automáticamente de todos los grupos de Telegram
usando la Telegram Client API (Telethon)
"""

import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramGroupLeaver:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('session_name', api_id, api_hash)

    async def connect(self):
        """Conectar al cliente de Telegram"""
        try:
            await self.client.start(phone=self.phone_number)
            logger.info("✅ Successfully connected to Telegram")
            
            # Mostrar información del usuario
            me = await self.client.get_me()
            logger.info(f"🤖 Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'No username'})")
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False

    async def get_all_dialogs(self):
        """Obtener todos los diálogos (chats, grupos, canales)"""
        try:
            dialogs = await self.client.get_dialogs()
            return dialogs
        except Exception as e:
            logger.error(f"❌ Error getting dialogs: {e}")
            return []

    async def leave_group(self, dialog):
        """Salir de un grupo específico"""
        try:
            entity = dialog.entity
            
            # Obtener información del grupo
            if hasattr(entity, 'title'):
                group_name = entity.title
            else:
                group_name = "Unknown Group"
            
            group_id = entity.id
            
            logger.info(f"📤 Attempting to leave: {group_name} (ID: {group_id})")
            
            # Intentar salir del grupo/canal
            if isinstance(entity, Channel):
                # Para canales y supergrupos
                await self.client.delete_dialog(entity)
                logger.info(f"✅ Successfully left channel/supergroup: {group_name}")
            elif isinstance(entity, Chat):
                # Para grupos normales
                await self.client.delete_dialog(entity)
                logger.info(f"✅ Successfully left group: {group_name}")
            else:
                logger.warning(f"⚠️ Unknown entity type for: {group_name}")
                return False
                
            return True
            
        except ChatAdminRequiredError:
            logger.warning(f"⚠️ Admin rights required to leave: {group_name}")
            return False
        except UserNotParticipantError:
            logger.info(f"ℹ️ Already not a participant of: {group_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error leaving {group_name}: {e}")
            return False

    async def leave_all_groups(self, exclude_names=None, dry_run=False):
        """
        Salir de todos los grupos
        
        Args:
            exclude_names: Lista de nombres de grupos a excluir
            dry_run: Si es True, solo muestra qué grupos se saldrían sin hacerlo realmente
        """
        exclude_names = exclude_names or []
        
        logger.info("🚀 Starting group leaving process...")
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
        
        # Obtener todos los diálogos
        dialogs = await self.get_all_dialogs()
        
        if not dialogs:
            logger.warning("📝 No dialogs found")
            return
        
        # Filtrar solo grupos y canales
        groups = []
        for dialog in dialogs:
            entity = dialog.entity
            
            # Verificar si es un grupo o canal
            if isinstance(entity, (Channel, Chat)):
                # Excluir chats privados
                if isinstance(entity, Channel) and entity.broadcast:
                    continue  # Saltar canales de broadcast
                
                # Verificar si está en la lista de exclusiones
                group_name = getattr(entity, 'title', 'Unknown')
                if group_name not in exclude_names:
                    groups.append(dialog)
        
        logger.info(f"📊 Found {len(groups)} groups/channels to process")
        
        if not groups:
            logger.info("ℹ️ No groups found to leave")
            return
        
        # Mostrar lista de grupos
        logger.info("📋 Groups/channels to leave:")
        for i, dialog in enumerate(groups, 1):
            entity = dialog.entity
            group_name = getattr(entity, 'title', 'Unknown')
            group_type = "Channel" if isinstance(entity, Channel) else "Group"
            logger.info(f"   {i}. {group_name} ({group_type})")
        
        if dry_run:
            logger.info("🔍 DRY RUN completed - no changes made")
            return
        
        # Confirmación del usuario
        print(f"\n⚠️ You are about to leave {len(groups)} groups/channels!")
        confirm = input("Are you sure you want to continue? (yes/no): ").lower().strip()
        
        if confirm not in ['yes', 'y']:
            logger.info("❌ Operation cancelled by user")
            return
        
        # Salir de cada grupo
        success_count = 0
        failed_count = 0
        
        for i, dialog in enumerate(groups, 1):
            entity = dialog.entity
            group_name = getattr(entity, 'title', 'Unknown')
            
            logger.info(f"📤 [{i}/{len(groups)}] Processing: {group_name}")
            
            success = await self.leave_group(dialog)
            if success:
                success_count += 1
            else:
                failed_count += 1
            
            # Esperar un poco entre requests para evitar rate limiting
            await asyncio.sleep(2)
        
        # Resumen final
        logger.info(f"\n✨ Process completed!")
        logger.info(f"✅ Successfully left: {success_count} groups")
        logger.info(f"❌ Failed to leave: {failed_count} groups")

    async def disconnect(self):
        """Desconectar del cliente"""
        await self.client.disconnect()
        logger.info("👋 Disconnected from Telegram")

async def main():
    # Configuración - Reemplaza con tus datos
    API_ID = 'YOUR_API_ID'  # Obtener de https://my.telegram.org
    API_HASH = 'YOUR_API_HASH'  # Obtener de https://my.telegram.org
    PHONE_NUMBER = 'YOUR_PHONE_NUMBER'  # Ej: '+1234567890'
    
    # Verificar configuración
    if API_ID == 'YOUR_API_ID' or API_HASH == 'YOUR_API_HASH' or PHONE_NUMBER == 'YOUR_PHONE_NUMBER':
        print("❌ Please configure your API credentials!")
        print("📝 To get API credentials:")
        print("   1. Go to https://my.telegram.org")
        print("   2. Log in with your phone number")
        print("   3. Go to 'API development tools'")
        print("   4. Create a new application")
        print("   5. Copy API ID and API Hash")
        return
    
    # Grupos a excluir (opcional)
    EXCLUDE_GROUPS = [
        "Important Group",
        "Family Chat",
        # Agregar nombres de grupos que NO quieres abandonar
    ]
    
    # Crear cliente
    leaver = TelegramGroupLeaver(API_ID, API_HASH, PHONE_NUMBER)
    
    try:
        # Conectar
        if await leaver.connect():
            # Ejecutar en modo dry-run primero (recomendado)
            print("🔍 Running in DRY RUN mode first...")
            await leaver.leave_all_groups(exclude_names=EXCLUDE_GROUPS, dry_run=True)
            
            # Preguntar si quiere ejecutar realmente
            print("\n" + "="*50)
            real_run = input("Do you want to proceed with the actual leaving? (yes/no): ").lower().strip()
            
            if real_run in ['yes', 'y']:
                await leaver.leave_all_groups(exclude_names=EXCLUDE_GROUPS, dry_run=False)
            else:
                print("❌ Operation cancelled")
    
    except KeyboardInterrupt:
        logger.info("⚠️ Operation cancelled by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        await leaver.disconnect()

if __name__ == "__main__":
    # Instalar dependencias:
    # pip install telethon
    
    asyncio.run(main())