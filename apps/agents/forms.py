from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML
from .models import AgentConfiguration, Provider, ProviderCategory, Brand

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
            
    class Meta:
        model = Provider
        fields = ['name', 'phone', 'city', 'category', 'brands']
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
            'category': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione una categoría'
            }),
        }
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.agent_config:
            instance.agent_config = self.agent_config
        if commit:
            instance.save()
            self.save_m2m()  # This is needed for many-to-many fields
        return instance