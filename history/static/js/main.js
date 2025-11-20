// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏错误提示
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        }, 3000);
    });

    // 处理星座选择后加载卫星列表（用于卫星关联表单）
    const constellationSelect = document.getElementById('constellation_id');
    if (constellationSelect) {
        constellationSelect.addEventListener('change', function() {
            const constellationId = this.value;
            if (constellationId) {
                // 加载该星座下的卫星
                fetch(`/satellites/by-constellation/${constellationId}`)
                    .then(response => response.json())
                    .then(satellites => {
                        const sat1Select = document.getElementById('satellite_id1');
                        const sat2Select = document.getElementById('satellite_id2');

                        // 清空并添加选项
                        [sat1Select, sat2Select].forEach(select => {
                            select.innerHTML = '<option value="">-- 请选择卫星 --</option>';
                            satellites.forEach(sat => {
                                const option = document.createElement('option');
                                option.value = sat.id;
                                option.textContent = `卫星 ${sat.satellite_id}`;
                                select.appendChild(option);
                            });
                        });
                    });
            }
        });

        // 初始加载已选星座的卫星
        if (constellationSelect.value) {
            constellationSelect.dispatchEvent(new Event('change'));
        }
    }
});