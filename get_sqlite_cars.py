import tornado.escape
import tornado.ioloop
import tornado.web
import sqlite3
import re


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
        if param['where_all'] or param['horsepower']:

            colums = {'model_list': 'model_list.ModelId, '
                                    'model_list.Maker, '
                                    'model_list.Model',
                      'car_names': 'car_names.MakeId, '
                                   'car_names.Model, '
                                   'car_names.MakeDescription',
                      'continents': 'continents.ContId, '
                                    'continents.Continent',
                      'countries': 'countries.CountryId, '
                                   'countries.CountryName, '
                                   'countries.Continent',
                      'car_makers': 'car_makers.Id, '
                                    'car_makers.maker, '
                                    'car_makers.FullName, '
                                    'car_makers.Country',
                      'car_data': 'car_data.Id, '
                                  'car_data.MPG, '
                                  'car_data.Cylinders, '
                                  'car_data.Edispl, '
                                  'car_data.Horsepower, '
                                  'car_data.Weight, '
                                  'car_data.Accelerate, '
                                  'car_data.Year'

                      }

            big_table = 'car_names JOIN model_list  ON model_list.model = car_names.model ' \
                        'JOIN car_makers ON car_makers.id = model_list.maker ' \
                        'JOIN countries  ON countries.countryid = car_makers.country ' \
                        'JOIN car_data ON car_names.MakeId = car_data.Id'

            querry = 'SELECT {} FROM {} {} {} {} {} '.format(colums[table],
                                                             big_table,
                                                             param['where_all'],
                                                             param['sort'],
                                                             param['horsepower'],
                                                             param['pages'])
        else:
            querry = 'SELECT * FROM {} {} {} {} '.format(table, param['where_one'], param['sort'], param['pages'])
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
    tables = {'model_list': ['Model', 'ModelId'],
              'car_names': ['Model', 'MakeId'],
              'continents': ['Continent', 'ContId'],
              'countries': ['CountryName', 'CountryId'],
              'car_makers': ['Maker', 'Id'],
              'car_data': ['Year', 'Id']
              }

    def sort(self, table):
        sort = self.get_argument('sort', None, True)

        sort_list = {'name': 'ORDER BY {}.{} ASC'.format(table, Parameters.tables[table][0]),
                     '-name': 'ORDER BY {}.{} DESC'.format(table, Parameters.tables[table][0]),
                     'id': 'ORDER BY {}.{} ASC'.format(table, Parameters.tables[table][1]),
                     '-id': 'ORDER BY {}.{} DESC'.format(table, Parameters.tables[table][1])}
        return sort_list.get(sort, '')

    def page(self):
        page = self.get_argument('page', 1, True)
        per_page = self.get_argument('per_page', 5, True)

        try:
            page = int(page)
            if page < 1:
                page = 1
        except ValueError:
            page = 1

        try:
            per_page = int(per_page)
            if per_page < 1:
                per_page = 5
        except ValueError:
            per_page = 5

        pages = 'LIMIT {} OFFSET {}'.format(per_page, (page - 1) * per_page)

        return pages

    def where_all(self, table):
        where_all = self.get_argument('where_all', '', True)
        if where_all:
            all = 'WHERE {}.{} = \'\'\'{}\'\'\''.format(table, Parameters.tables[table][0], where_all)
        else:
            all = ''

        return all

    def where_one(self, table):
        where_one = self.get_argument('where_one', '', True)
        if where_one:
            one = 'WHERE {}.{} = \'\'\'{}\'\'\''.format(table, Parameters.tables[table][0], where_one)
        else:
            one = ''

        return one

    def get_param(self, table):
        sort = Parameters.sort(self, table)
        pages = Parameters.page(self)
        where_all = Parameters.where_all(self, table)
        where_one = Parameters.where_one(self, table)
        horsepower = self.get_argument('horsepower', '', True)

        if horsepower:
            a = str(horsepower)
            b = re.findall(r'\d+', a)
            if len(b) == 3 and b[0] < b[2] < b[1]:
                power = 'AND car_data.Horsepower BETWEEN {} AND {} AND NOT car_data.Horsepower = {}'.format(b[0], b[1], b[2])
            elif len(b) == 2 and b[0] < b[1]:
                power = 'AND car_data.Horsepower BETWEEN {} AND {}'.format(b[0], b[1])
            else:
                power = ''

        ret = {'sort': sort,
               'pages': pages,
               'where_all': where_all,
               'where_one': where_one,
               'horsepower': power}

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


class CarsDataHandler(Parameters):
    def get(self):
        paramet = self.get_param('car_data')
        data = MY_DB_fecthall.table('car_data', paramet)
        if not data:
            raise tornado.web.HTTPError(404)
        data_list = []
        for i in data:
            data_list.append({
                'Id': i[0],
                'MPG': i[1],
                'Cylinders': i[2],
                'Edispl': i[3],
                'Horsepower': i[4],
                'Weight': i[5],
                'Accelerate': i[6],
                'Year': i[7]
            })
        response = {'data': data_list}
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


class CarDataHandler(tornado.web.RequestHandler):
    def get(self, id):
        data_id = MY_DB_fecthone.table('car_data', 'Id', id)
        if not data_id:
            raise tornado.web.HTTPError(404)
        response = {
               'Id': data_id[0],
                'MPG': data_id[1],
                'Cylinders': data_id[2],
                'Edispl': data_id[3],
                'Horsepower': data_id[4],
                'Weight': data_id[5],
                'Accelerate': data_id[6],
                'Year': data_id[7]
            }
        self.write(response)


application = tornado.web.Application([

    #Адрес всей таблицы
    (r"/models", ModelsHandler),
    (r"/car-names", CarNamesHandler),
    (r"/continent", ContinentsHandler),
    (r"/countries", CountriesHandler),
    (r"/car-makers", CarMakersHandler),
    (r"/car-data", CarsDataHandler),

    #Адрес для id
    (r"/models/([0-9]+)", ModelHandler),
    (r"/car-names/([0-9]+)", CarNameHandler),
    (r"/continent/([0-9]+)", ContinentHandler),
    (r"/countries/([0-9]+)", CountryHandler),
    (r"/car-makers/([0-9]+)", CarMakerHandler),
    (r"/car-data/([0-9]+)", CarDataHandler)


])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()