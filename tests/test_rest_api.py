from webtest import TestApp
from yubiauth.rest_api import application

app = TestApp(application)


# Users


def test_create_user():
    resp = app.post('/users', {'username': 'user1', 'password': 'foo'},
                    status=303)
    user = resp.follow().json
    assert user['name'] == 'user1'
    assert user['id'] == 1
    app.post('/users', {'username': 'user2', 'password': 'bar'},
             status=303)
    app.post('/users', {'username': 'user3', 'password': 'baz'},
             status=303)

    assert len(app.get('/users').json) == 3


def test_delete_user_by_id():
    id = app.post('/users', {'username': 'redshirt', 'password': 'llap'},
                  status=303).follow().json['id']

    app.delete('/users/%d' % id)
    app.get('/users/%d' % id, status=404)


def test_delete_user_by_name():
    name = app.post('/users', {'username': 'redshirt', 'password': 'llap'},
                    status=303).follow().json['name']

    app.delete('/users/%s' % name.encode('ascii'))
    app.get('/users/%s' % name, status=404)


def test_delete_user_by_post():
    id = app.post('/users', {'username': 'redshirt', 'password': 'llap'},
                  status=303).follow().json['id']

    app.post('/users/%d/delete' % id)
    app.get('/users/%d' % id, status=404)


def test_get_user_by_id():
    resp = app.get('/users/1', status=200)
    user = resp.json
    assert user['id'] == 1
    assert user['name'] == 'user1'


def test_get_user_by_name():
    resp = app.get('/users/user1')
    user = resp.json
    assert user['id'] == 1
    assert user['name'] == 'user1'


def test_authenticate_user_get():
    resp = app.get('/authenticate?username=user1&password=foo')
    user = resp.json
    assert user['name'] == 'user1'


def test_authenticate_user_post():
    resp = app.post('/authenticate', {'username': 'user1', 'password': 'foo'})
    user = resp.json
    assert user['name'] == 'user1'


def test_reset_password():
    app.get('/authenticate?username=user1&password=foo')
    app.post('/users/1/reset', {'password': 'foobar'})

    app.get('/authenticate?username=user1&password=foo', status=401)
    app.get('/authenticate?username=user1&password=foobar')


def test_create_user_with_existing_username():
    app.post('/users', {'username': 'user1', 'password': 'bar'}, status=500)


def test_authenticate_with_invalid_username():
    app.post('/authenticate', {'username': 'notauser',
                               'password': 'foo'}, status=401)
    app.post('/authenticate', {'username': 'notauser'}, status=400)


def test_authenticate_with_invalid_password():
    app.post('/authenticate', {'username': 'user1',
                               'password': 'wrongpassword'}, status=401)
    app.post('/authenticate', {'username': 'user1'}, status=400)


def test_get_user_by_invalid_username():
    assert app.get('/users/notauser', status=404)


# YubiKeys


PREFIX_1 = 'ccccccccccce'
PREFIX_2 = 'cccccccccccd'
PREFIX_3 = 'cccccccccccf'


def test_bind_yubikeys():
    resp = app.get('/users/1/yubikeys')
    yubikeys = resp.json
    assert len(yubikeys) == 0

    app.post('/users/1/yubikeys', {'yubikey': PREFIX_1})
    resp = app.get('/users/1/yubikeys')
    yubikeys = resp.json
    assert yubikeys == [PREFIX_1]

    app.post('/users/1/yubikeys', {'yubikey': PREFIX_2})
    app.post('/users/2/yubikeys', {'yubikey': PREFIX_2})

    resp = app.get('/users/1/yubikeys')
    yubikeys = resp.json
    assert sorted(yubikeys) == sorted([PREFIX_1, PREFIX_2])

    resp = app.get('/users/1')
    user = resp.json
    assert sorted(user['yubikeys']) == sorted([PREFIX_1, PREFIX_2])

    resp = app.get('/users/2')
    user = resp.json
    assert user['yubikeys'] == [PREFIX_2]


def test_show_yubikey():
    resp = app.get('/users/1/yubikeys/%s' % PREFIX_1)
    yubikey = resp.json
    assert yubikey['enabled']
    assert yubikey['prefix'] == PREFIX_1


def test_show_yubikey_for_wrong_user():
    app.get('/users/2/yubikeys/%s' % PREFIX_1, status=404)


def test_unbind_yubikeys():
    app.delete('/users/1/yubikeys/%s' % PREFIX_1)
    resp = app.get('/users/1/yubikeys')
    yubikeys = resp.json
    assert yubikeys == [PREFIX_2]


def test_authenticate_without_yubikey():
    app.get('/authenticate?username=user2&password=bar', status=401)


# Attributes


def test_assign_attributes():
    app.post('/users/1/attributes', {'key': 'attr1', 'value': 'val1'})
    app.post('/users/1/attributes', {'key': 'attr2', 'value': 'val2'})

    resp = app.get('/users/1/attributes')
    attributes = resp.json
    assert attributes['attr1'] == 'val1'
    assert attributes['attr2'] == 'val2'
    assert len(attributes) == 2

    resp = app.get('/users/1')
    user = resp.json
    assert user['attributes'] == attributes


def test_read_attribute():
    resp = app.get('/users/1/attributes/attr1')
    assert resp.json == 'val1'


def test_read_missing_attribute():
    resp = app.get('/users/1/attributes/foo')
    assert not resp.json


def test_overwrite_attributes():
    app.post('/users/1/attributes', {'key': 'attr1', 'value': 'newval'})
    resp = app.get('/users/1/attributes')
    attributes = resp.json

    assert attributes['attr1'] == 'newval'
    assert attributes['attr2'] == 'val2'
    assert len(attributes) == 2


def test_unset_attributes():
    app.delete('/users/1/attributes/attr1')
    resp = app.get('/users/1/attributes')
    attributes = resp.json

    assert attributes['attr2'] == 'val2'
    assert len(attributes) == 1

    resp = app.get('/users/1/attributes/attr1')
    assert not resp.json


def _basic_attribute_test(base_url):
    values = {
        'attr1': 'foo',
        'attr2': 'bar',
        'attr3': 'baz',
    }

    for key, value in values.items():
        app.post(base_url, {'key': key, 'value': value})
        assert app.get('%s/%s' % (base_url, key)).json == value

    app.delete('%s/attr2' % (base_url))
    assert not app.get('%s/attr2' % base_url).json

    app.post(base_url, {'key': 'attr3', 'value': 'newval'})
    assert app.get('%s/attr3' % base_url).json == 'newval'

    del values['attr2']
    values['attr3'] = 'newval'
    assert app.get(base_url).json == values


def test_user_attributes():
    _basic_attribute_test('/users/1/attributes')
    _basic_attribute_test('/users/2/attributes')


def test_yubikey_attributes():
    _basic_attribute_test('/yubikeys/%s/attributes' % PREFIX_1)
    _basic_attribute_test('/users/2/yubikeys/%s/attributes' % PREFIX_2)