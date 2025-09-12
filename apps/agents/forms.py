from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field
from .models import AgentConfiguration, Provider

class AgentConfigurationForm(forms.ModelForm):
    class Meta:
        model = AgentConfiguration
        fields = ['configuration_data']
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

class ProviderForm(forms.ModelForm):
    class Meta:
        model = Provider
        fields = ['name', 'phone', 'city']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del proveedor'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de teléfono',
                'data-mask': '(000) 000-0000'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad'
            }),
        }
        labels = {
            'name': 'Nombre',
            'phone': 'Teléfono',
            'city': 'Ciudad',
        }
        help_texts = {
            'phone': 'Formato: (XXX) XXX-XXXX',
        }
