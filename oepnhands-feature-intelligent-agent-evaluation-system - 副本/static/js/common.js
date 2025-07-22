// 通用JavaScript函数

// API请求封装
class API {
    static async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    static async get(url) {
        return this.request(url, { method: 'GET' });
    }

    static async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    static async postForm(url, formData) {
        return this.request(url, {
            method: 'POST',
            headers: {},
            body: formData,
        });
    }

    static async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
}

// 消息提示
class Message {
    static show(text, type = 'info', duration = 3000) {
        const messageContainer = this.getContainer();
        const messageElement = document.createElement('div');
        messageElement.className = `alert alert-${type}`;
        messageElement.textContent = text;
        
        messageContainer.appendChild(messageElement);
        
        // 自动移除
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, duration);
    }

    static success(text, duration = 3000) {
        this.show(text, 'success', duration);
    }

    static error(text, duration = 5000) {
        this.show(text, 'error', duration);
    }

    static warning(text, duration = 4000) {
        this.show(text, 'warning', duration);
    }

    static info(text, duration = 3000) {
        this.show(text, 'info', duration);
    }

    static getContainer() {
        let container = document.getElementById('message-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'message-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }
}

// 加载状态管理
class Loading {
    static show(element, text = '加载中...') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.disabled = true;
            element.innerHTML = `<span class="loading"></span> ${text}`;
        }
    }

    static hide(element, originalText = '提交') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.disabled = false;
            element.innerHTML = originalText;
        }
    }
}

// 进度条管理
class ProgressBar {
    constructor(element) {
        if (typeof element === 'string') {
            this.element = document.querySelector(element);
        } else {
            this.element = element;
        }
        this.bar = this.element.querySelector('.progress-bar');
    }

    setProgress(percentage) {
        if (this.bar) {
            this.bar.style.width = `${Math.min(100, Math.max(0, percentage))}%`;
        }
    }

    show() {
        if (this.element) {
            this.element.classList.remove('hidden');
        }
    }

    hide() {
        if (this.element) {
            this.element.classList.add('hidden');
        }
    }
}

// 文件上传处理
class FileUpload {
    constructor(element, options = {}) {
        this.element = typeof element === 'string' ? document.querySelector(element) : element;
        this.options = {
            multiple: true,
            accept: '.docx,.xlsx',
            maxSize: 50 * 1024 * 1024, // 50MB
            ...options
        };
        
        this.init();
    }

    init() {
        if (!this.element) return;

        // 创建隐藏的文件输入
        this.fileInput = document.createElement('input');
        this.fileInput.type = 'file';
        this.fileInput.multiple = this.options.multiple;
        this.fileInput.accept = this.options.accept;
        this.fileInput.style.display = 'none';
        
        this.element.appendChild(this.fileInput);

        // 点击事件
        this.element.addEventListener('click', (e) => {
            if (e.target !== this.fileInput) {
                this.fileInput.click();
            }
        });

        // 文件选择事件
        this.fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });

        // 拖拽事件
        this.element.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.element.classList.add('dragover');
        });

        this.element.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.element.classList.remove('dragover');
        });

        this.element.addEventListener('drop', (e) => {
            e.preventDefault();
            this.element.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });
    }

    handleFiles(files) {
        const validFiles = [];
        
        for (let file of files) {
            if (this.validateFile(file)) {
                validFiles.push(file);
            }
        }

        if (validFiles.length > 0) {
            this.onFilesSelected(validFiles);
        }
    }

    validateFile(file) {
        // 检查文件大小
        if (file.size > this.options.maxSize) {
            Message.error(`文件 ${file.name} 太大，最大支持 ${this.options.maxSize / 1024 / 1024}MB`);
            return false;
        }

        // 检查文件类型
        const allowedTypes = this.options.accept.split(',').map(type => type.trim());
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            Message.error(`文件 ${file.name} 类型不支持，支持的类型：${this.options.accept}`);
            return false;
        }

        return true;
    }

    onFilesSelected(files) {
        // 子类重写此方法
        console.log('Files selected:', files);
    }

    getFiles() {
        return this.fileInput.files;
    }
}

// 任务状态轮询
class TaskPoller {
    constructor(taskId, onUpdate, onComplete, interval = 2000) {
        this.taskId = taskId;
        this.onUpdate = onUpdate;
        this.onComplete = onComplete;
        this.interval = interval;
        this.polling = false;
    }

    start() {
        if (this.polling) return;
        
        this.polling = true;
        this.poll();
    }

    stop() {
        this.polling = false;
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
    }

    async poll() {
        if (!this.polling) return;

        try {
            const task = await API.get(`/api/tasks/${this.taskId}`);
            
            if (this.onUpdate) {
                this.onUpdate(task);
            }

            if (task.status === 'completed' || task.status === 'failed') {
                this.polling = false;
                if (this.onComplete) {
                    this.onComplete(task);
                }
                return;
            }

            // 继续轮询
            this.timeoutId = setTimeout(() => this.poll(), this.interval);
            
        } catch (error) {
            console.error('Task polling error:', error);
            this.timeoutId = setTimeout(() => this.poll(), this.interval);
        }
    }
}

// 表格排序
class TableSorter {
    constructor(table) {
        this.table = typeof table === 'string' ? document.querySelector(table) : table;
        this.init();
    }

    init() {
        if (!this.table) return;

        const headers = this.table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sort(header.dataset.sort, header);
            });
        });
    }

    sort(column, header) {
        const tbody = this.table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const columnIndex = Array.from(header.parentNode.children).indexOf(header);
        
        const isAscending = header.classList.contains('sort-asc');
        
        // 清除所有排序类
        this.table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });

        // 添加当前排序类
        header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');

        // 排序行
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();
            
            // 尝试数字比较
            const aNum = parseFloat(aValue);
            const bNum = parseFloat(bValue);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAscending ? bNum - aNum : aNum - bNum;
            } else {
                return isAscending ? bValue.localeCompare(aValue) : aValue.localeCompare(bValue);
            }
        });

        // 重新插入排序后的行
        rows.forEach(row => tbody.appendChild(row));
    }
}

// 工具函数
const Utils = {
    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // 格式化日期
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN');
    },

    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // 节流函数
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // 复制到剪贴板
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            Message.success('已复制到剪贴板');
        } catch (err) {
            console.error('复制失败:', err);
            Message.error('复制失败');
        }
    }
};

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 设置当前页面的导航高亮
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-item a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // 初始化所有表格排序
    document.querySelectorAll('table[data-sortable]').forEach(table => {
        new TableSorter(table);
    });
});