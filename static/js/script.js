var profileId = '';

$(document).ready(() => {
    loadGameDetails();
});

function loadGameDetails() {
    profileId = $("meta[name=profile]").attr("content");
    $('.progress').show();
    fetch('/user/' + profileId + '/games').then(response => {
        if (response.status == 200) {
            response
                .json()
                .then((games) => {
                    //console.log(games);
                    buildTable(games);
                });
        }
    });
    $('.progress').hide();
}

function buildTable(games) {
    console.log('building table...');
    games.forEach(game => {
        console.log('Building row for ' + game);

        let app_id = game.app_id
        let game_data = game.game_data
        let newRow = $('<tr id="' + app_id + '"></tr>');
        let imgCell = $('<td></td>');
        imgCell.append($('<a></a>').attr('href', 'http://store.steampowered.com/app/' + app_id).append($('<img></img>').attr('src', game_data.image).addClass('table-img')));

        let titleCell = $('<td></td>').text(game_data.title);
        let genreCell = $('<td></td>').text(game_data.genre);

        let price = '';
        if (game_data.price != '0.00') {
            price = '$' + game_data.price;
        } else {
            price = 'Free';
        }

        let priceCell = $('<td></td>').text(price);

        let playedtime = ((game.played_time / 60).toFixed(2) + ' hours');
        let playtimeCell = $('<td></td>').text(playedtime);

        newRow
            .append(imgCell)
            .append(titleCell)
            .append(genreCell)
            .append(priceCell)
            .append(playtimeCell);

        $('#games table').append(newRow);
    });
    $('.progress').hide();
}