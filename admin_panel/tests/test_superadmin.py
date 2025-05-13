#!/usr/bin/env python
import os
import django
import sys

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

def test_admin_protection():
    """测试ID为1的管理员用户是否受到保护"""
    # 创建一个测试用户
    try:
        test_user = User.objects.create_user(username='test_protection_user', password='test123')
        print(f"创建测试用户: {test_user.username} (ID: {test_user.id})")
        
        # 尝试删除测试用户
        test_user.delete()
        print("✓ 成功删除测试用户")
        
        # 尝试删除ID为1的管理员用户
        try:
            admin_user = User.objects.get(id=1)
            print(f"找到ID为1的用户: {admin_user.username}")
            admin_user.delete()
            print("✗ 错误: 能够删除ID为1的管理员用户")
            return False
        except PermissionDenied as e:
            print(f"✓ 保护机制正常工作: {str(e)}")
            return True
        except User.DoesNotExist:
            print("✗ 错误: ID为1的用户不存在")
            return False
        except Exception as e:
            print(f"✗ 出现意外错误: {str(e)}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n===== 测试超级管理员保护机制 =====")
    success = test_admin_protection()
    if success:
        print("\n✓ 测试通过: ID为1的超级管理员受到了保护\n")
        sys.exit(0)
    else:
        print("\n✗ 测试失败: ID为1的超级管理员保护机制不正常\n")
        sys.exit(1) 