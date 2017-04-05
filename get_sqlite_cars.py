import tornado.escape
import tornado.ioloop
import tornado.web
import sqlite3


class connection_database_fecthone(object):
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()

    def table(self, table, column, id):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM {} WHERE {} = (?)'.format(table, column), (str(id), ))
        data_model = cur.fetchone()
        if not data_model:
            return None
        else:
            return data_model

    def __del__(self):
        self.conn.close()


MY_DB_fecthone = connection_database_fecthone('cars_sql.db')


class connection_database_fecthall(connection_database_fecthone):
    def __init__(self, db):
        connection_database_fecthone.__init__(self, db)

    def table(self, table, param):
        cur = self.conn.cursor()
        if param['country']:
            colums = {'model_list': 'model_list.ModelId, model_list.Maker, model_list.Model',
                      'car_names': 'car_names.MakeId, car_names.Model, car_names.MakeDescription',
                      'continents': 'continents.ContId, continents.Continent',
                      'countries': 'countries.CountryId, countries.CountryName, countries.Continent',
                      'car_makers': 'car_makers.Id, car_makers.maker, car_makers.FullName, car_makers.Country'
                      }
            big_table = 'car_names JOIN model_list  ON model_list.model = car_names.model JOIN car_makers ON car_makers.id = model_list.maker JOIN countries  ON countries.countryid = car_makers.country'
            querry = 'SELECT {} FROM {} {} {} {} '.format(colums[table], big_table, param['country'], param['sort'], param['pages'])
        else:
            querry = 'SELECT * FROM {} {} {} {} '.format(table,  param['model'], param['sort'], param['pages'])
        print(querry)
        cur.execute(querry)
        data_model = cur.fetchall()
        if not data_model:
            return None
        else:
            return data_model

    def __del__(self):
        self.conn.close()


MY_DB_fecthall = connection_database_fecthall('cars_sql.db')


# Класс с параметрами
class Parameters(tornado.web.RequestHandler):
    def get_param(self, table):
        param = self.get_argument('sort', None, True)
        page = self.get_argument('page', 1, True)
        per_page = self.get_argument('per_page', 5, True)
        model_in = self.get_argument('model', '', True)
        country = self.get_argument('country', '', True)

        tables = {'model_list': ['Model', 'ModelId'],
                  'car_names' : ['Model', 'MakeId'],
                  'continents' : ['Continent', 'ContId'],
                  'countries' : ['CountryName', 'CountryId'],
                  'car_makers' : ['Maker', 'Id']
                  }
        # sort
        sort = {}
        sort['name'] = 'ORDER BY {} ASC'.format(tables[table][0])
        sort['-name'] = 'ORDER BY {} DESC'.format(tables[table][0])
        sort['id'] = 'ORDER BY {} ASC'.format(tables[table][1])
        sort['-id'] = 'ORDER BY {} DESC'.format(tables[table][1])
        sort[None] = ''

        # page
        try:
            page = int(page)
            if page < 1:
                page = 1
        except TypeError:
            page = 1

        try:
            per_page = int(per_page)
            if per_page < 1:
                per_page = 5
        except TypeError:
            per_page = 5

        pages = 'LIMIT {} OFFSET {}'.format(per_page, (page - 1) * per_page)


        if model_in:
            model = 'WHERE model = \'\'\'{}\'\'\''.format(model_in)
        else:
            model = ''

        if country:
            country = 'WHERE countries.CountryName = \'\'\'{}\'\'\''.format(country)
        else:
            country = ''


        ret = {
            'sort': sort[param],
            'pages': pages,
            'model': model,
            'country': country
               }
        return ret



# Хендлер для вывода всей таблицы
class ModelsHandler(Parameters):
    def get(self):
        paramet = self.get_param('model_list')
        model = MY_DB_fecthall.table('model_list', paramet)
        if not model:
            raise tornado.web.HTTPError(404)
        model_list = []
        for i in model:
            model_list.append({
                'id': i[0],
                'Maker': i[1],
                'Model': i[2]
            })
        response = {'models': model_list}
        self.write(response)


class CarNamesHandler(Parameters):
    def get(self):
        paramet = self.get_param('car_names')
        car_names = MY_DB_fecthall.table('car_names', paramet)
        if not car_names:
            raise tornado.web.HTTPError(404)
        cars_list = []
        for i in car_names:
            cars_list.append({
                'id': i[0],
                'Model': i[1],
                'Make Description': i[2]
            })
        response = {'car_names': cars_list}
        self.write(response)


class ContinentsHandler(Parameters):
    def get(self):
        paramet = self.get_param('continents')
        cont = MY_DB_fecthall.table('continents', paramet)
        if not cont:
            raise tornado.web.HTTPError(404)
        cont_list = []
        for i in cont:
            cont_list.append({
                'id': i[0],
                'Continent': i[1]
            })
        response = {'models': cont_list}
        self.write(response)


class CountriesHandler(Parameters):
    def get(self):
        paramet = self.get_param('countries')
        country = MY_DB_fecthall.table('countries', paramet)
        if not country:
            raise tornado.web.HTTPError(404)
        country_list = []
        for i in country:
            country_list.append({
                'CountryId': i[0],
                'CountryName': i[1],
                'CountryContinent': i[2]
            })
        response = {'models': country_list}
        self.write(response)


class CarMakersHandler(Parameters):
    def get(self):
        paramet = self.get_param('car_makers')
        car_makers = MY_DB_fecthall.table('car_makers', paramet)
        if not car_makers:
            raise tornado.web.HTTPError(404)
        car_makers_list = []
        for i in car_makers:
            car_makers_list.append({
                'id': i[0],
                'Maker': i[1],
                'FullName': i[2],
                'Country': i[3]
            })
        response = {'models': car_makers_list}
        self.write(response)



# Хендлер для вывода по id
class CarMakerHandler(tornado.web.RequestHandler):
    def get(self, id):
        car_makers_id = MY_DB_fecthone.table('car_makers', 'Id', id)
        if not car_makers_id:
            raise tornado.web.HTTPError(404)
        response = {
            'id': car_makers_id[0],
            'Maker': car_makers_id[1],
            'FullName': car_makers_id[2],
            'Country': car_makers_id[3]
        }
        self.write(response)


class CountryHandler(tornado.web.RequestHandler):
    def get(self, id):
        country_id = MY_DB_fecthone.table('countries', 'CountryId', id)
        if not country_id:
            raise tornado.web.HTTPError(404)
        response = {
            'CountryId': country_id[0],
            'CountryName': country_id[1],
            'CountryContinent': country_id[2]
        }
        self.write(response)


class ContinentHandler(tornado.web.RequestHandler):
    def get(self, id):
        cont_id = MY_DB_fecthone.table('continents', 'ContId', id)
        if not cont_id:
            raise tornado.web.HTTPError(404)
        response = {
            'id': cont_id[0],
            'Continent': cont_id[1]
        }
        self.write(response)


class CarNameHandler(tornado.web.RequestHandler):
    def get(self, id):
        cars_id = MY_DB_fecthone.table('car_names', 'MakeId', id)
        if not cars_id:
            raise tornado.web.HTTPError(404)
        response = {
            'id': cars_id[0],
            'Model': cars_id[1],
            'Make Description': cars_id[2]
        }
        self.write(response)


class ModelHandler(tornado.web.RequestHandler):
    def get(self, id):
        model_id = MY_DB_fecthone.table('model_list', 'ModelId', id)
        if not model_id:
            raise tornado.web.HTTPError(404)
        response = {
            'id': model_id[0],
            'Maker': model_id[1],
            'Model': model_id[2]
        }
        self.write(response)




application = tornado.web.Application([

    #Адрес всей таблицы
    (r"/models", ModelsHandler),
    (r"/car-names", CarNamesHandler),
    (r"/continent", ContinentsHandler),
    (r"/countries", CountriesHandler),
    (r"/car-makers", CarMakersHandler),

    #Адрес для id
    (r"/models/([0-9]+)", ModelHandler),
    (r"/car-names/([0-9]+)", CarNameHandler),
    (r"/continent/([0-9]+)", ContinentHandler),
    (r"/countries/([0-9]+)", CountryHandler),
    (r"/car-makers/([0-9]+)", CarMakerHandler)

])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()