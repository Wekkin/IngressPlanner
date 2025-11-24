/**
 * Ingress Intel Portal提取器 - 浏览器扩展脚本
 * 
 * 使用方法：
 * 1. 在Ingress Intel页面（https://intel.ingress.com/intel）打开浏览器控制台（F12）
 * 2. 复制此脚本到控制台并执行
 * 3. 脚本会自动提取当前可见区域的Portal
 * 4. 复制输出的JSON数据
 */

(function() {
    'use strict';
    
    console.log('Ingress Portal提取器已启动...');
    
    // 等待Intel地图加载
    function waitForIntel() {
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                if (window.portalDetail && window.map) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 500);
        });
    }
    
    // 从Intel API获取Portal
    function fetchPortals() {
        return new Promise((resolve) => {
            if (!window.map) {
                resolve([]);
                return;
            }
            
            const bounds = window.map.getBounds();
            const zoom = window.map.getZoom();
            
            // 计算tile范围
            function deg2num(lat_deg, lon_deg, zoom) {
                const lat_rad = lat_deg * Math.PI / 180.0;
                const n = Math.pow(2.0, zoom);
                const xtile = Math.floor((lon_deg + 180.0) / 360.0 * n);
                const ytile = Math.floor((1.0 - Math.log(Math.tan(lat_rad) + (1 / Math.cos(lat_rad))) / Math.PI) / 2.0 * n);
                return [xtile, ytile];
            }
            
            function num2key(x, y, z) {
                let key = '';
                for (let i = z; i > 0; i--) {
                    let digit = 0;
                    const mask = 1 << (i - 1);
                    if ((x & mask) !== 0) digit += 1;
                    if ((y & mask) !== 0) digit += 2;
                    key += digit.toString();
                }
                return key;
            }
            
            const minTile = deg2num(bounds.getSouth(), bounds.getWest(), zoom);
            const maxTile = deg2num(bounds.getNorth(), bounds.getEast(), zoom);
            
            const tileKeys = [];
            for (let x = minTile[0]; x <= maxTile[0]; x++) {
                for (let y = minTile[1]; y <= maxTile[1]; y++) {
                    tileKeys.push(num2key(x, y, zoom));
                }
            }
            
            // 获取Portal数据
            const batchSize = 50;
            const allPortals = [];
            
            function fetchBatch(index) {
                if (index >= tileKeys.length) {
                    resolve(allPortals);
                    return;
                }
                
                const batch = tileKeys.slice(index, index + batchSize);
                const url = 'https://intel.ingress.com/intel/tile/getEntities';
                const params = new URLSearchParams({ tileKeys: batch.join(',') });
                
                fetch(url + '?' + params)
                    .then(response => response.json())
                    .then(data => {
                        if (data.result) {
                            data.result.forEach(tile => {
                                if (tile.gameEntities) {
                                    tile.gameEntities.forEach(entity => {
                                        if (entity[2] === 'p') { // 'p'表示Portal
                                            try {
                                                const portalData = typeof entity[3] === 'string' 
                                                    ? JSON.parse(entity[3]) 
                                                    : entity[3];
                                                
                                                allPortals.push({
                                                    guid: entity[0],
                                                    name: portalData.title || 'Unknown',
                                                    lat: portalData.latE6 / 1e6,
                                                    lon: portalData.lngE6 / 1e6,
                                                    image: portalData.image
                                                });
                                            } catch (e) {
                                                console.error('解析Portal失败:', e);
                                            }
                                        }
                                    });
                                }
                            });
                        }
                        
                        // 继续下一批
                        setTimeout(() => fetchBatch(index + batchSize), 500);
                    })
                    .catch(error => {
                        console.error('获取Portal失败:', error);
                        resolve(allPortals);
                    });
            }
            
            fetchBatch(0);
        });
    }
    
    // 导出Portal数据
    function exportPortals(portals) {
        // 去重（基于GUID）
        const uniquePortals = [];
        const seen = new Set();
        
        portals.forEach(portal => {
            if (!seen.has(portal.guid)) {
                seen.add(portal.guid);
                uniquePortals.push(portal);
            }
        });
        
        // 生成TXT格式
        let txtContent = '# 从Ingress Intel提取的Portal坐标\n';
        txtContent += '# 格式：name,lat,lon\n\n';
        
        uniquePortals.forEach(portal => {
            txtContent += `${portal.name},${portal.lat},${portal.lon}\n`;
        });
        
        // 生成JSON格式
        const jsonContent = JSON.stringify(uniquePortals, null, 2);
        
        // 输出到控制台
        console.log('='.repeat(60));
        console.log(`找到 ${uniquePortals.length} 个Portal`);
        console.log('='.repeat(60));
        console.log('\nTXT格式（可直接保存为.txt文件）:');
        console.log(txtContent);
        console.log('\nJSON格式:');
        console.log(jsonContent);
        
        // 复制到剪贴板
        if (navigator.clipboard) {
            navigator.clipboard.writeText(txtContent).then(() => {
                console.log('\n✓ 已复制TXT格式到剪贴板');
            });
        }
        
        // 显示下载链接
        const blob = new Blob([txtContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'ingress_portals.txt';
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        console.log('\n✓ 已自动下载 portals.txt 文件');
    }
    
    // 主函数
    async function main() {
        try {
            await waitForIntel();
            console.log('正在提取Portal...');
            const portals = await fetchPortals();
            exportPortals(portals);
        } catch (error) {
            console.error('提取失败:', error);
        }
    }
    
    // 添加全局函数供手动调用
    window.extractIngressPortals = main;
    
    // 自动执行
    main();
})();

// 使用说明
console.log('\n使用说明:');
console.log('1. 在Ingress Intel地图上导航到目标区域');
console.log('2. 脚本会自动提取当前可见区域的所有Portal');
console.log('3. 数据会显示在控制台并自动下载');
console.log('4. 如需手动执行，请运行: window.extractIngressPortals()');

