filepath = r'c:\Users\Hp\OneDrive\Desktop\STYLE-HUB\style_hub\user\profile\views.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_editprofile = False
for line in lines:
    if 'def editprofile_page' in line:
        in_editprofile = True
    elif 'def verify_changed_email' in line:
        in_editprofile = False
        
    if in_editprofile and "return redirect('editprofile')" in line:
        line = line.replace("return redirect('editprofile')", "return render(request, 'editprofile.html', {'old_data': request.POST})")
    
    new_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done!')
