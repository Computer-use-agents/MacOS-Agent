import Quartz
import time
import subprocess
import tempfile
import json

import ApplicationServices
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
import numpy as np
from PIL import Image
from importlib.resources import files
from pathlib import Path

class GetTree():
    name = 'get_accessibility_tree'
    description = "A tool can get the accessibility tree and screen shot of a application"
    inputs = {
        "application": {"description": "the name of the application", "type": "string" }
    }
    output_type = "list"

    # save_path=str(files("finder_agent").joinpath("save"))+'/'
    save_path = str(Path('macosagent/agents/finder_agent/finder_agent').joinpath("save"))+'/'
    if not Path(save_path).exists():
        Path(save_path).mkdir(parents=True, exist_ok=True)

    def get_accessibility_tree(self, element, level=0, max_depth=10):
        """递归获取元素的accessibility tree, 返回树形结构"""
        if level >= max_depth or not element:
            return None
            
        try:
            node = {
                'level': level,
                'children': [],
                'attributes': {}
            }
            
            # 获取元素的角色
            err, role = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXRoleAttribute, None
            )
            if err == 0:
                node['role'] = role
            
            # 获取标题
            err, title = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXTitleAttribute, None
            )
            if err == 0 and title:
                node['title'] = title
                
            # 检查是否可交互
            err, can_press = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXPressAction, None
            )
            err, can_focus = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXFocusedAttribute, None
            )
            
            node['is_interactive'] = (
                role in ['AXButton', 'AXLink', 'AXTextField', 'AXTextArea', 'AXCheckBox', 
                        'AXRadioButton', 'AXComboBox', 'AXSlider', 'AXMenu', 'AXMenuItem', 
                        'AXPopUpButton'] or 
                can_press == True or 
                can_focus == True
            )
            
            # 获取所有属性
            err, attributes = ApplicationServices.AXUIElementCopyAttributeNames(element, None)
            if err == 0:
                for attr in attributes:
                    if attr not in [ApplicationServices.kAXRoleAttribute, ApplicationServices.kAXTitleAttribute]:
                        err, value = ApplicationServices.AXUIElementCopyAttributeValue(element, attr, None)
                        if err == 0:
                            node['attributes'][attr] = str(value)
            
            # 递归获取子元素
            err, children = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXChildrenAttribute, None
            )
            if err == 0 and children:
                for child in children:
                    child_node = self.get_accessibility_tree(child, level + 1, max_depth)
                    if child_node:
                        node['children'].append(child_node)
                        
            return node
                    
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def capture_window_screenshot(self, window_id):
        """使用替代方法捕获窗口截图"""
        temp_file = tempfile.mktemp('.png')
        try:
            subprocess.run(['screencapture', '-l', str(window_id), '-o', temp_file], check=True)
            return Image.open(temp_file)
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        finally:
            try:
                import os
                os.remove(temp_file)
            except:
                pass

    def get_app_windows(self, app_name):
        """获取指定应用的窗口和accessibility tree"""
        try:
            workspace = ApplicationServices.NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            target_app = None
            for app in running_apps:
                if app.localizedName() == app_name:
                    target_app = app
                    break
            
            if not target_app:
                return None
                
            # 尝试激活应用
            target_app.activateWithOptions_(0)
            
            # 给应用一点时间来激活
            time.sleep(1)
                
            pid = target_app.processIdentifier()
            app = ApplicationServices.AXUIElementCreateApplication(pid)
            
            # 获取窗口列表
            err, windows = ApplicationServices.AXUIElementCopyAttributeValue(
                app, ApplicationServices.kAXWindowsAttribute, None
            )
            if err == 0 and windows:
                window_trees = []  # 存储所有窗口的树形结构
                
                # 获取窗口信息
                window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                for i, window in enumerate(windows):
                    if i != 1:
                        continue                    
                    try:
                        tree = self.get_accessibility_tree(window)
                        window_trees.append(tree)
                    except Exception as e:
                        print(f"An error occurred: {e}")
                    
                    # 查找对应的窗口ID并截图
                    for window_info in window_list:
                        if window_info.get(Quartz.kCGWindowOwnerPID) == pid:
                            window_id = window_info.get(Quartz.kCGWindowNumber)
                            screenshot = self.capture_window_screenshot(window_id)
                            if screenshot:
                                screenshot.save(self.save_path+f"{app_name}_window.png")
                    
                return window_trees  # 返回所有窗口的树形结构
            
            return None
            
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def forward (self, application):
        trees = self.get_app_windows(application)
        if trees:
            with open(self.save_path+application+'_accessibility_tree.json', 'w', encoding='utf-8') as f:
                json.dump(trees, f, ensure_ascii=False, indent=2)
        return [self.save_path+f"{application}_window.png", self.save_path+application+'_accessibility_tree.json']
