from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML
from .models import AgentConfiguration, Provider, ProviderCategory, Brand, Product, ProductCategory, ProductBrand, AutomotiveCenterInfo

class AgentConfigurationForm(forms.ModelForm):
    class Meta:
        model = AgentConfiguration
        fields = ['configuration_data', 'enable_providers']
        widgets = {
            'configuration_data': forms.Textarea(attrs={
                'rows': 10,
                'placeholder': 'Ingrese la configuración en formato JSON'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Guardar Configuración', css_class='btn btn-dark'))

        self.fields['configuration_data'].label = 'Configuración'
        self.fields['configuration_data'].help_text = 'Ingrese los parámetros de configuración en formato JSON'

        # Restrict enable_providers, enable_products and enable_automotive_info based on agent name
        if self.instance and self.instance.pk and 'MechAI' not in self.instance.agent.name:
            self.fields['enable_providers'].disabled = True
            self.fields['enable_providers'].help_text = 'Solo disponible para agentes MechAI'
            self.fields['enable_products'].disabled = True
            self.fields['enable_products'].help_text = 'Solo disponible para agentes MechAI'
            self.fields['enable_automotive_info'].disabled = True
            self.fields['enable_automotive_info'].help_text = 'Solo disponible para agentes MechAI'

    def clean(self):
        cleaned_data = super().clean()
        enable_providers = cleaned_data.get('enable_providers')
        enable_products = cleaned_data.get('enable_products')
        enable_automotive_info = cleaned_data.get('enable_automotive_info')
        if enable_providers or enable_products or enable_automotive_info:
            if self.instance.pk:
                agent = self.instance.agent
            else:
                agent_id = cleaned_data.get('agent')
                if agent_id:
                    from .models import Agent
                    agent = Agent.objects.get(pk=agent_id)
                else:
                    agent = None
            if agent and 'MechAI' not in agent.name:
                raise forms.ValidationError("La gestión de proveedores, productos e información del centro automotriz solo está disponible para agentes MechAI")
        return cleaned_data

class ProviderCategoryForm(forms.ModelForm):
    class Meta:
        model = ProviderCategory
        fields = ['name']  # Only include fields that should be editable
        
    def __init__(self, *args, **kwargs):
        self.agent_config = kwargs.pop('agent_config', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.agent_config:
            instance.agent_config = self.agent_config
        if commit:
            instance.save()
        return instance

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la marca'
            }),
        }
        labels = {
            'name': 'Nombre de la marca',
        }

    def __init__(self, *args, **kwargs):
        self.agent_config = kwargs.pop('agent_config', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.agent_config:
            instance.agent_config = self.agent_config
        if commit:
            instance.save()
        return instance

class ProviderForm(forms.ModelForm):
    class Meta:
        model = Provider
        fields = ['name', 'phone', 'city', 'category', 'brands']

    def __init__(self, *args, **kwargs):
        self.agent_config = kwargs.pop('agent_config', None)
        super().__init__(*args, **kwargs)

        # Filter categories and brands by agent_config
        if self.agent_config:
            self.fields['category'].queryset = ProviderCategory.objects.filter(
                agent_config=self.agent_config
            )

            # Update the brands field to use CheckboxSelectMultiple
            self.fields['brands'].widget = forms.CheckboxSelectMultiple()
            self.fields['brands'].queryset = Brand.objects.filter(
                agent_config=self.agent_config
            )
            self.fields['brands'].required = False
            
class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.agent_config = kwargs.pop('agent_config', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.agent_config:
            instance.agent_config = self.agent_config
        if commit:
            instance.save()
        return instance

class ProductBrandForm(forms.ModelForm):
    class Meta:
        model = ProductBrand
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la marca'
            }),
        }
        labels = {
            'name': 'Nombre de la marca',
        }

    def __init__(self, *args, **kwargs):
        self.agent_config = kwargs.pop('agent_config', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.agent_config:
            instance.agent_config = self.agent_config
        if commit:
            instance.save()
        return instance

class ProductForm(forms.ModelForm):
    image_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://ejemplo.com/imagen.jpg',
            'id': 'id_image_url'
        }),
        label='URL de la imagen'
    )

    def __init__(self, *args, **kwargs):
        self.agent_config = kwargs.pop('agent_config', None)
        super().__init__(*args, **kwargs)

        # Filter categories and brand by agent_config
        if self.agent_config:
            self.fields['category'].queryset = ProductCategory.objects.filter(
                agent_config=self.agent_config
            )

            self.fields['brand'].queryset = ProductBrand.objects.filter(
                agent_config=self.agent_config
            )

        # Set initial values based on upload method
        if self.instance and self.instance.pk:
            if self.instance.image_upload_method == 'url' and self.instance.image_url:
                self.fields['image_url'].initial = self.instance.image_url

    def clean(self):
        cleaned_data = super().clean()
        upload_method = cleaned_data.get('image_upload_method')
        image_file = cleaned_data.get('image')
        image_url = cleaned_data.get('image_url')

        # Only validate if this is a new form submission (not editing existing)
        if not self.instance.pk:
            if upload_method == 'file' and not image_file:
                raise forms.ValidationError("Debe seleccionar un archivo de imagen.")
            elif upload_method == 'url' and not image_url:
                raise forms.ValidationError("Debe proporcionar una URL de imagen válida.")

        return cleaned_data

    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'image_upload_method', 'image', 'image_url', 'category', 'brand']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del producto'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del producto',
                'rows': 4
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'image_upload_method': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'id_image_file'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione una categoría'
            }),
            'brand': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione una marca'
            }),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.agent_config:
            instance.agent_config = self.agent_config
        if commit:
            instance.save()
        return instance

class AutomotiveCenterInfoForm(forms.ModelForm):
    # Campos consolidados para horarios
    weekdays_open = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label='Hora de apertura')
    weekdays_close = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label='Hora de cierre')
    saturday_open = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label='Hora de apertura')
    saturday_close = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label='Hora de cierre')
    sunday_holidays_open = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label='Hora de apertura')
    sunday_holidays_close = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label='Hora de cierre')

    class Meta:
        model = AutomotiveCenterInfo
        fields = ['physical_address']
        widgets = {
            'physical_address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa del taller',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Guardar Información del Centro', css_class='btn btn-primary'))

        # Load existing business hours
        if self.instance and self.instance.pk and self.instance.business_hours:
            hours = self.instance.business_hours

            # Set weekdays (Monday-Friday) - use Monday as reference
            if 'monday' in hours:
                self.fields['weekdays_open'].initial = hours['monday'].get('open')
                self.fields['weekdays_close'].initial = hours['monday'].get('close')

            # Set Saturday
            if 'saturday' in hours:
                self.fields['saturday_open'].initial = hours['saturday'].get('open')
                self.fields['saturday_close'].initial = hours['saturday'].get('close')

            # Set Sunday/Holidays
            if 'sunday' in hours:
                self.fields['sunday_holidays_open'].initial = hours['sunday'].get('open')
                self.fields['sunday_holidays_close'].initial = hours['sunday'].get('close')

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Build business hours from form data
        business_hours = {}

        # Weekdays (Monday-Friday)
        weekdays_open = self.cleaned_data.get('weekdays_open')
        weekdays_close = self.cleaned_data.get('weekdays_close')
        if weekdays_open and weekdays_close:
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                business_hours[day] = {
                    'open': str(weekdays_open),
                    'close': str(weekdays_close)
                }

        # Saturday
        saturday_open = self.cleaned_data.get('saturday_open')
        saturday_close = self.cleaned_data.get('saturday_close')
        if saturday_open and saturday_close:
            business_hours['saturday'] = {
                'open': str(saturday_open),
                'close': str(saturday_close)
            }

        # Sunday and Holidays
        sunday_holidays_open = self.cleaned_data.get('sunday_holidays_open')
        sunday_holidays_close = self.cleaned_data.get('sunday_holidays_close')
        if sunday_holidays_open and sunday_holidays_close:
            business_hours['sunday'] = {
                'open': str(sunday_holidays_open),
                'close': str(sunday_holidays_close)
            }

        instance.business_hours = business_hours

        if commit:
            instance.save()
        return instance
