$(document).ready(() => {

    // format playtime values
    $('td.playtime').each((idx) => {
        let target = $($('td.playtime')[idx])
        let gamePlaytime = parseInt(target.text());
        let result = '';
        if (gamePlaytime >= 60) {
            result = (((gamePlaytime / 60).toFixed(1)).toString() + ' hours');
        } else if (gamePlaytime > 0) {
            result = (gamePlaytime.toString()) + ' mins';
        } else {
            result = 'Never played'
        }
        target.text(result)
    });

    // format price values
    $('td.price').each((idx) => {
        let target = $($('td.price')[idx])
        let gamePrice = target.text();
        let result = target.text();
        if (gamePrice == '$0.00') {
            result = 'Free'
        }
        target.text(result)
    });

    // data table for sorting/pagination
    $('#games table').DataTable();
});