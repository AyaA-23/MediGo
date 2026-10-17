from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid


@csrf_exempt
def upload_image_chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    consultation_id = request.POST.get('consultation_id')
    expediteur = request.POST.get('expediteur', 'patient')
    image = request.FILES.get('image')

    if not image:
        return JsonResponse({'error': 'Aucune image'}, status=400)

    ext = os.path.splitext(image.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return JsonResponse({'error': 'Format non supporté'}, status=400)

    filename = f"chat/{uuid.uuid4()}{ext}"
    path = default_storage.save(filename, ContentFile(image.read()))
    url = f"/media/{path}"

    from apps.consultations.models import Consultation
    from .models import Message, ImageMedicale
    try:
        consultation = Consultation.objects.get(id=consultation_id)
        # Sauvegarder dans Message (chat)
        Message.objects.create(
            consultation=consultation,
            contenu=f'[IMAGE]{url}',
            expediteur=expediteur,
            est_alerte_urgente=False
        )
        # Sauvegarder dans ImageMedicale (dossier consultation)
        source = request.POST.get('source', 'chat')  # 'chat' ou 'camera'
        nom = f"{'📷 Photo' if source == 'camera' else '🖼️ Image'}_{expediteur}_{uuid.uuid4().hex[:8]}{ext}"
        ImageMedicale.objects.create(
            consultation=consultation,
            storage_key=path,
            nom_original=nom,
            file_type=ext.lstrip('.'),
            file_size=image.size if hasattr(image, 'size') else None,
        )
    except Exception as e:
        pass

    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()

    payload = {
        'type': 'chat_message',
        'message': f'[IMAGE]{url}',
        'expediteur': expediteur,
    }

    try:
        consultation = Consultation.objects.get(id=consultation_id)
        patient_code = consultation.patient.code_unique
        medecin_id = consultation.medecin_id
        async_to_sync(channel_layer.group_send)(f'patient_{patient_code}', payload)
        if medecin_id:
            async_to_sync(channel_layer.group_send)(f'medecin_{medecin_id}', payload)
    except Exception:
        pass

    return JsonResponse({'status': 'ok', 'url': url})
