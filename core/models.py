import os
from django.db import models
from utils.images import process_image, BANNER_IMAGE_MAX


class Banner(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    subtitle = models.CharField('Подзаголовок', max_length=300, blank=True)
    button_text = models.CharField('Текст кнопки', max_length=50, blank=True)
    button_link = models.CharField('Ссылка кнопки', max_length=200, blank=True)
    image = models.ImageField('Изображение (обязательно)', upload_to='hero/')
    image_mobile = models.ImageField('Изображение для мобильных', upload_to='hero/', blank=True)
    video = models.FileField('Видео (MP4/WebM)', upload_to='hero/videos/', blank=True,
                             help_text='Видео играет на десктопе. На мобильных — фото.')
    is_active = models.BooleanField('Активен', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'
        ordering = ['order']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Delete old files when replaced
        if self.pk:
            try:
                old = Banner.objects.get(pk=self.pk)
                for field_name in ('image', 'image_mobile', 'video'):
                    old_file = getattr(old, field_name)
                    new_file = getattr(self, field_name)
                    if old_file and old_file != new_file:
                        if os.path.isfile(old_file.path):
                            os.remove(old_file.path)
            except Banner.DoesNotExist:
                pass

        for field_name in ('image', 'image_mobile'):
            field = getattr(self, field_name)
            # Only process newly uploaded files (not already saved ones)
            if field and hasattr(field.file, 'content_type'):
                try:
                    path, content = process_image(field, 'banners/', max_size=BANNER_IMAGE_MAX)
                    field.save(path, content, save=False)
                except (ValueError, Exception):
                    pass
        super().save(*args, **kwargs)


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'

    def __str__(self):
        return self.email