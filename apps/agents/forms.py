from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field
from .models import AgentConfiguration

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
