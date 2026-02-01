from django import forms

class RegisterForm(forms.Form):
    first_name =forms.CharField(max_length=100,
                error_messages={
                    "required":"يرجى ادخال الاسم الاول",
                    "max_length":"يرجى ادخال الايميل",
                })
    last_name =forms.CharField(max_length=100,
                error_messages={
                    "required":"يرجى ادخال الاسم الاخير",
                    "max_length":"يرجى ادخال الايميل",
                })
    email = forms.EmailField(max_length=100,
                             error_messages={
            'required': 'يجب ادخال الايميل',
            'max_length': 'يجب ادخال الايميل بشكل صحيح',
        },)
    username = forms.CharField(max_length=100,
                             error_messages={
            'required': 'يجب ادخال اسم المستخدم',
            'max_length': 'يجب ادخال اسم المستخدم بشكل صحيح',
        },)
    password = forms.CharField(min_length=8,
        widget=forms.PasswordInput,
        error_messages={
            'required': 'يجب ادخال كلمة المرور',
            'min_length': 'يجب ادخال كلمة المرور بشكل صحيح',
        },
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
            error_messages={
            'required': 'يجب ادخال تاكيد كلمة المرور',
            'min_length': 'يجب ادخال تاكيد كلمة المرور بشكل صحيح',
        },
    )

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100,
                             error_messages={
            "invalid": "يرجى ادخال اسم مستخدم صحيح",
            'required': 'يجب ادخال اسم المستخدم',
            'max_length': 'يجب ادخال اسم المستخدم بشكل صحيح  ',
        },)
    password = forms.CharField(min_length=8,
        widget=forms.PasswordInput,
        error_messages={
            'required': 'يجب ادخال كلمة المرور',
            'min_length': 'يجب ادخال كلمة المرور بشكل صحيح',
        },
    )