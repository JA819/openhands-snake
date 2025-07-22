class FileUpload {
    constructor(elementId, options = {}) {
        this.element = document.getElementById(elementId);
        this.options = {
            accept: '.docx',
            multiple: true,
            maxSize: 10 * 1024 * 1024,
            ...options
        };
        this.files = [];
        this.init();
    }

    init() {
        this.createUploadZone();
        this.bindEvents();
    }

    createUploadZone() {
        this.fileInput = document.createElement('input');
        this.fileInput.type = 'file';
        this.fileInput.accept = this.options.accept;
        this.fileInput.multiple = this.options.multiple;
        this.fileInput.style.display = 'none';

        this.uploadZone = document.createElement('div');
        this.uploadZone.className = 'file-upload-zone';
        this.uploadZone.innerHTML = `
            <div class="file-upload-text">点击或拖曳上传DOCX文件（支持多文件）</div>
            <button type="button" class="file-upload-button">选择文件</button>
        `;

        this.fileList = document.createElement('div');
        this.fileList.className = 'file-list';

        this.element.appendChild(this.fileInput);
        this.element.appendChild(this.uploadZone);
        this.element.appendChild(this.fileList);
    }

    bindEvents() {
        this.uploadZone.addEventListener('click', () => this.fileInput.click());

        this.fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));

        this.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadZone.classList.add('dragover');
        });

        this.uploadZone.addEventListener('dragleave', () => {
            this.uploadZone.classList.remove('dragover');
        });

        this.uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadZone.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });
    }

    handleFiles(fileList) {
        Array.from(fileList).forEach(file => {
            if (file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
                if (file.size <= this.options.maxSize) {
                    this.files.push(file);
                    this.updateFileList();
                } else {
                    alert(`文件 ${file.name} 超过大小限制`);
                }
            } else {
                alert(`文件 ${file.name} 格式不正确，请上传DOCX文件`);
            }
        });
    }

    updateFileList() {
        if (this.files.length === 0) {
            this.fileList.innerHTML = '未选择文件';
            return;
        }

        this.fileList.innerHTML = this.files.map((file, index) => `
            <div class="file-item">
                <span class="file-name">${file.name}</span>
                <span class="remove-file" data-index="${index}">
                    <i class="fas fa-times"></i>
                </span>
            </div>
        `).join('');

        this.fileList.querySelectorAll('.remove-file').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.currentTarget.dataset.index);
                this.files.splice(index, 1);
                this.updateFileList();
            });
        });
    }

    getFiles() {
        return this.files;
    }

    clear() {
        this.files = [];
        this.updateFileList();
    }
}