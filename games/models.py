from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
import hashlib
import uuid
import time


class Category(models.Model):
    """Game category model"""
    name = models.CharField(_('Category Name'), max_length=100)
    slug = models.SlugField(_('URL Slug'), max_length=100, unique=True)
    description = models.TextField(_('Category Description'), blank=True)
    parent = models.ForeignKey('self', verbose_name=_('Parent Category'), null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='children')
    image = models.ImageField(verbose_name=_('Category Image'), upload_to='categories/', null=True, blank=True)
    icon_class = models.CharField(_('Icon Class'), max_length=100, blank=True, help_text=_('Font Awesome 6+ icon class, e.g., "fa-solid fa-gamepad"'))
    order = models.IntegerField(_('Sort Order'), default=0)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['id']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Override save method to automatically generate unique hash string as slug
        Use Django's slugify function to ensure URL-friendly format
        """
        if not self.slug or self.slug.strip() == '':
            # Generate unique hash string as slug
            self.slug = self._generate_unique_hash_slug()

        super().save(*args, **kwargs)

    def _generate_unique_hash_slug(self):
        """
        Generate unique hash string as slug
        Combine category name, timestamp and UUID to ensure uniqueness
        """
        # Create raw string for hashing, including category name, timestamp and random UUID
        raw_string = f"{self.name}-{time.time()}-{uuid.uuid4().hex}"

        # Generate hash value using SHA256
        hash_object = hashlib.sha256(raw_string.encode('utf-8'))
        hash_hex = hash_object.hexdigest()

        # Take first 12 characters as slug (short enough and highly unique)
        hash_slug = hash_hex[:12]

        # Use Django's slugify to ensure the generated hash string is URL-friendly
        # Although hash strings are usually URL-friendly, this is safer
        slug = slugify(hash_slug)

        # Double-check uniqueness (hash collision probability is extremely low in theory, but for safety)
        counter = 1
        original_slug = slug
        while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = slugify(f"{original_slug}-{counter}")
            counter += 1

        return slug


class Game(models.Model):
    """Game model"""
    title = models.CharField(_('Game Title'), max_length=200)
    slug = models.SlugField(_('URL Slug'), max_length=200, unique=True)
    description = models.TextField(_('Game Description'))
    iframe_url = models.URLField(_('Game iframe URL'))
    thumbnail = models.ImageField(verbose_name=_('Game Thumbnail'), upload_to='games/', null=True, blank=True)
    categories = models.ManyToManyField(Category, verbose_name=_('Game Categories'), related_name='games')
    content = models.TextField(_('Game Content'), blank=True)
    is_featured = models.BooleanField(_('Is Featured'), default=False)
    is_active = models.BooleanField(_('Is Active'), default=True)
    view_count = models.PositiveIntegerField(_('View Count'), default=0)
    rating = models.DecimalField(_('Rating'), max_digits=3, decimal_places=1, default=0)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Game')
        verbose_name_plural = _('Games')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

    @property
    def rating_int(self):
        """Return the integer part of the rating"""
        return int(self.rating)

    @property
    def rating_int_plus_half(self):
        """Return the integer part of the rating + 0.5, used for displaying half stars"""
        return int(self.rating) + 1 if self.rating % 1 >= 0.5 else None


class Advertisement(models.Model):
    """Advertisement model"""
    POSITION_CHOICES = (
        ('header', _('Header')),
        ('sidebar', _('Sidebar')),
        ('game_between', _('Between Games')),
        ('footer', _('Footer')),
    )

    AD_TYPE_CHOICES = (
        ('display', _('Display Ad')),
        ('text', _('Text Ad')),
        ('native', _('Native Ad')),
        ('interstitial', _('Interstitial Ad')),
        ('video', _('Video Ad')),
    )

    AD_SIZE_CHOICES = (
        ('728x90', '728 x 90 (Leaderboard)'),
        ('300x250', '300 x 250 (Medium Rectangle)'),
        ('320x50', '320 x 50 (Mobile Banner)'),
        ('300x600', '300 x 600 (Half Page)'),
        ('970x250', '970 x 250 (Billboard)'),
        ('320x480', '320 x 480 (Mobile Interstitial)'),
        ('responsive', _('Responsive')),
        ('custom', _('Custom Size')),
    )

    # Basic information
    name = models.CharField(_('Advertisement Name'), max_length=100)
    position = models.CharField(_('Position'), max_length=20, choices=POSITION_CHOICES)
    ad_type = models.CharField(_('Ad Type'), max_length=20, choices=AD_TYPE_CHOICES, default='display')
    ad_size = models.CharField(_('Ad Size'), max_length=20, choices=AD_SIZE_CHOICES, default='responsive')

    # Advertisement content
    image = models.ImageField(verbose_name=_('Advertisement Image'), upload_to='ads/', null=True, blank=True)
    url = models.URLField(_('Advertisement URL'), blank=True)
    html_code = models.TextField(_('HTML Code'), blank=True, help_text=_('Fill this field if using third-party advertisement code'))

    # Google AdSense related fields
    adsense_unit_id = models.CharField(_('AdSense Unit ID'), max_length=100, blank=True, help_text=_('Google AdSense ad unit ID'))
    adsense_publisher_id = models.CharField(_('AdSense Publisher ID'), max_length=100, blank=True, help_text=_('Google AdSense publisher ID'))
    adsense_slot_id = models.CharField(_('AdSense Slot ID'), max_length=100, blank=True, help_text=_('Google AdSense slot ID'))

    # Status and time
    is_active = models.BooleanField(_('Active'), default=True)
    start_date = models.DateTimeField(_('Start Date'), null=True, blank=True)
    end_date = models.DateTimeField(_('End Date'), null=True, blank=True)

    # Statistics data
    click_count = models.PositiveIntegerField(_('Click Count'), default=0)
    view_count = models.PositiveIntegerField(_('View Count'), default=0)
    revenue = models.DecimalField(_('Revenue'), max_digits=10, decimal_places=2, default=0.00, help_text=_('Total revenue generated'))
    ctr = models.DecimalField(_('Click Through Rate'), max_digits=5, decimal_places=2, default=0.00, help_text=_('Click through rate percentage'))

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Advertisement')
        verbose_name_plural = _('Advertisements')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_position_display(self):
        """Return the display name of the position"""
        for code, name in self.POSITION_CHOICES:
            if code == self.position:
                return name
        return self.position

    def has_image(self):
        """Check if the advertisement has an image"""
        return bool(self.image)

    def calculate_ctr(self):
        """Calculate click-through rate"""
        if self.view_count > 0:
            self.ctr = (self.click_count / self.view_count) * 100
        else:
            self.ctr = 0
        return self.ctr

    def get_ad_code(self):
        """Get advertisement code"""
        if self.html_code:
            return self.html_code
        elif self.adsense_unit_id and self.adsense_publisher_id:
            # Generate Google AdSense code
            return f'''
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={self.adsense_publisher_id}" crossorigin="anonymous"></script>
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{self.adsense_publisher_id}"
     data-ad-slot="{self.adsense_slot_id}"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({{}});
</script>
            '''.strip()
        return ''





