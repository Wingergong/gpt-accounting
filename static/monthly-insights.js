(function (global) {
    const ALLOWED_CATEGORIES = ['早餐', '午餐', '晚餐', '咖啡饮料', '旅行', '教育', '超市', '网购', '其他'];
    const ALLOWED_CATEGORY_SET = new Set(ALLOWED_CATEGORIES);

    function normalizeAmount(value) {
        const amount = Number.parseFloat(value);
        return Number.isFinite(amount) ? amount : 0;
    }

    function filterAllowedMonthData(monthData) {
        return (monthData || []).filter(item => ALLOWED_CATEGORY_SET.has(item.category));
    }

    function getLatestThreeMonths(monthData) {
        const months = [...new Set(filterAllowedMonthData(monthData).map(item => item.month).filter(Boolean))].sort();
        return months.slice(-3);
    }

    function buildRecentThreeMonthComparison(monthData) {
        const filteredMonthData = filterAllowedMonthData(monthData);
        const months = getLatestThreeMonths(filteredMonthData);
        const categoryMap = new Map();

        filteredMonthData.forEach(item => {
            if (!months.includes(item.month)) {
                return;
            }
            if (!categoryMap.has(item.category)) {
                categoryMap.set(item.category, {
                    category: item.category,
                    valuesByMonth: Object.fromEntries(months.map(month => [month, 0])),
                });
            }
            const entry = categoryMap.get(item.category);
            entry.valuesByMonth[item.month] += normalizeAmount(item.amount);
        });

        const latestMonth = months[months.length - 1] || '';
        const categories = [...categoryMap.values()]
            .map(entry => {
                const values = months.map(month => Math.round(entry.valuesByMonth[month] * 100) / 100);
                const total = Math.round(values.reduce((sum, value) => sum + value, 0) * 100) / 100;
                const latestMonthAmount = latestMonth ? Math.round((entry.valuesByMonth[latestMonth] || 0) * 100) / 100 : 0;
                return {
                    category: entry.category,
                    values,
                    total,
                    average: months.length ? Math.round((total / months.length) * 100) / 100 : 0,
                    change: values.length >= 2 ? Math.round((values[values.length - 1] - values[0]) * 100) / 100 : 0,
                    latestMonthAmount,
                };
            })
            .sort((a, b) => b.latestMonthAmount - a.latestMonthAmount || b.total - a.total || a.category.localeCompare(b.category, 'zh-Hans-CN'))
            .slice(0, 3);

        return {
            months,
            latestMonth,
            latestMonthTopCategories: categories.map(item => item.category),
            categories,
        };
    }

    function generateOptimizationSuggestions(comparison) {
        const suggestions = [];
        const months = comparison?.months || [];
        const categories = comparison?.categories || [];

        if (!months.length || !categories.length) {
            return ['最近3个月的有效分类数据不足，建议先补充规范分类后的月度数据，再生成趋势建议。'];
        }

        const topCategory = categories[0];
        suggestions.push(`从最近${months.length}个月的有效分类看，${topCategory.category} 累计支出最高（¥${topCategory.total.toFixed(0)}），建议优先为该类别单独设定预算上限，并在下月重点跟踪。`);

        const risingCategory = [...categories]
            .filter(item => item.values.length >= 3 && item.values[item.values.length - 1] > item.values[0])
            .sort((a, b) => b.change - a.change)[0];
        if (risingCategory) {
            suggestions.push(`${risingCategory.category} 呈持续上升趋势（${months[0]} → ${months[months.length - 1]} 增加 ¥${risingCategory.change.toFixed(0)}），建议复盘最近一次大额消费场景，判断哪些支出可以前置规划或压缩。`);
        }

        const steadyCategory = categories
            .filter(item => item.values.length === months.length && item.values.every(value => value > 0))
            .sort((a, b) => b.average - a.average)[0];
        if (steadyCategory) {
            suggestions.push(`${steadyCategory.category} 已连续 ${months.length} 个月发生支出，适合拆成固定月预算并按周复盘执行情况，避免月底集中超支。`);
        }

        while (suggestions.length < 3) {
            suggestions.push('建议优先关注近3个月累计最高的前3个类别，先做预算封顶，再观察下月是否出现回落。');
        }

        return suggestions.slice(0, 3);
    }

    function getTrendLabel(item) {
        if ((item?.change || 0) > 0) {
            return item.latestMonthAmount >= item.total * 0.6 ? '持续上升' : '快速增长';
        }
        if ((item?.change || 0) < 0) {
            return '阶段回落';
        }
        return '本月抬升';
    }

    function renderRecentThreeMonthInsights(comparison, options = {}) {
        const doc = options.document || global.document || (typeof document !== 'undefined' ? document : null);
        const getCategoryMeta = options.getCategoryMeta || global.getCategoryMeta || ((category) => ({ name: category, emoji: '🏷️', color: '#9ca3af' }));
        if (!doc) {
            return;
        }

        const summaryEl = doc.getElementById('recentThreeMonthSummary');
        const comparisonEl = doc.getElementById('recentThreeMonthComparison');
        const suggestionsEl = doc.getElementById('optimizationSuggestions');
        if (!summaryEl || !comparisonEl || !suggestionsEl) {
            return;
        }

        const months = comparison.months || [];
        const categories = comparison.categories || [];
        if (!months.length || !categories.length) {
            summaryEl.innerHTML = '<div class="text-sm text-gray-500">最近3个月有效分类数据不足，暂时无法生成对比。</div>';
            comparisonEl.innerHTML = '';
            suggestionsEl.innerHTML = '<li>暂无建议</li>';
            return;
        }

        const topThree = categories.slice(0, 3);
        const latestMonth = comparison.latestMonth || months[months.length - 1] || '';
        summaryEl.innerHTML = `
            <div class="insight-summary-card rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
                <div class="text-sm font-semibold text-slate-700 mb-1">${latestMonth} 当月花费 Top 3</div>
                <div class="text-sm text-slate-500">本月消费重心明显落在${topThree.map(item => item.category).join('、')}</div>
            </div>
        `;

        comparisonEl.innerHTML = `<div class="latest-month-top-three grid grid-cols-3 gap-4">${topThree.map((item, index) => {
            const meta = getCategoryMeta(item.category);
            const trendLabel = getTrendLabel(item);
            const maxValue = Math.max(...item.values, 1);
            const bars = item.values.map((value, monthIndex) => `
                <div class="flex-1 text-center">
                    <div class="text-[11px] text-slate-400 mb-2">${months[monthIndex]}</div>
                    <div class="mx-auto flex items-end" style="height:96px; width:100%;">
                        <div class="mx-auto rounded-t-[10px]" style="height:${Math.max((value / maxValue) * 96, 10)}px; background: linear-gradient(180deg, ${meta.color} 0%, rgba(255,255,255,0.92) 180%); width: 28px;"></div>
                    </div>
                    <div class="text-[11px] text-slate-600 mt-2">¥${value.toFixed(0)}</div>
                </div>
            `).join('');
            return `
                <div class="insight-card rounded-2xl border border-slate-200 bg-white p-4 shadow-sm min-w-0">
                    <div class="flex items-center justify-between mb-3 gap-3">
                        <div class="insight-rank text-xs font-semibold uppercase tracking-wide text-slate-400">Top ${index + 1}</div>
                        <div class="text-base font-semibold text-slate-900 truncate">${meta.emoji} ${meta.name}</div>
                    </div>
                    <div class="insight-label text-xs text-slate-400 mb-1">当月</div>
                    <div class="text-3xl font-bold text-slate-900 leading-none mb-3">¥${item.latestMonthAmount.toFixed(0)}</div>
                    <div class="text-sm text-slate-500 mb-4">累计 ¥${item.total.toFixed(0)}</div>
                    <div class="rounded-2xl bg-slate-50 px-3 py-3 mb-4">
                        <div class="flex items-end gap-2">${bars}</div>
                    </div>
                    <div class="insight-trend text-sm font-medium text-slate-600">${trendLabel}</div>
                </div>
            `;
        }).join('')}</div>`;

        const suggestions = generateOptimizationSuggestions(comparison);
        suggestionsEl.innerHTML = suggestions.map(item => `<li>${item}</li>`).join('');
    }

    async function loadRecentThreeMonthInsights(options = {}) {
        if (typeof fetch === 'undefined') {
            return;
        }
        const doc = options.document || global.document || (typeof document !== 'undefined' ? document : null);
        if (!doc) {
            return;
        }
        const response = await fetch('/monthData?month=');
        const monthData = await response.json();
        const comparison = buildRecentThreeMonthComparison(monthData);
        renderRecentThreeMonthInsights(comparison, options);
    }

    const api = {
        ALLOWED_CATEGORIES,
        filterAllowedMonthData,
        getLatestThreeMonths,
        buildRecentThreeMonthComparison,
        generateOptimizationSuggestions,
        renderRecentThreeMonthInsights,
        loadRecentThreeMonthInsights,
    };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = api;
    }

    global.MonthlyInsights = api;
})(typeof window !== 'undefined' ? window : globalThis);
