from flask import Flask, render_template, request, session, g, redirect, url_for
import bs4, json, sqlite3, time, pygal
import os as os
from bs4 import BeautifulSoup as soup
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.before_request
def before_request():
    if 'user' in session:
        g.user = session['user']
    else:
        g.user = None


@app.route("/login")
def login():
    if g.user:
        return render_template('home.html')
    else:
        return render_template('login.html')

@app.route("/login-process", methods=['POST'])
def loginPro():
    if request.method == 'POST':
        session.pop('user', None)
        conn = sqlite3.connect('voters.db')
        c = conn.cursor()

        username = request.form['username']
        password = request.form['password']

        c.execute("SELECT username, password FROM users WHERE username = '{}' AND password = '{}'".format(username, password))
        user = c.fetchall()

        if user:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            loginTry = True
            return render_template('login.html', loginTry=loginTry)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return render_template("login.html")

@app.route("/")
@app.route("/home")
def home():
    if g.user:
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route("/users")
def users():
    if g.user:
        conn = sqlite3.connect('voters.db')
        c = conn.cursor()

        c.execute("SELECT users.id, users.username, users.access FROM users")
        users = c.fetchall()


        return render_template("users.html", users=users)
    return redirect(url_for('login'))

@app.route("/user-profile", methods=['GET'])
def userProfile():
    if g.user:
        conn = sqlite3.connect('voters.db')
        c = conn.cursor()

        id = request.args.get('id')

        c.execute("SELECT username FROM users WHERE id ='{}'".format(id))
        userList = c.fetchall()
        username = userList[0][0]

        c.execute("SELECT count(*) FROM voter WHERE recordedBy = '{}'".format(id))
        scrapeCount = c.fetchall()
        scrapes     = scrapeCount[0][0]

        date = datetime.today().strftime('%m/%d/%Y')
        c.execute("SELECT count(*) FROM voter WHERE recordedBy = '{}' AND dateRecorded >= '{} 00:00:00' AND dateRecorded <= '{} 23:00:00'".format(id, date, date))
        scrapeCounts = c.fetchall()
        scrapers = scrapeCounts[0][0]

        return render_template("user-profile.html", username=username, scrapes=scrapes, scrapers=scrapers)
    else:
        return redirect(url_for('login'))

@app.route("/profile", methods=['GET'])
def profile():
    if g.user:
        conn = sqlite3.connect('voters.db')
        c = conn.cursor()

        id = request.args.get('id')

        # Gets name of voter
        c.execute("SELECT full_name, facebook_id FROM voter WHERE id ='{}'".format(id))
        nameList = c.fetchall()
        name = nameList[0][0]
        fbId = nameList[0][1]
        fbId = fbId.replace('fb://profile/', '')

        # Gets basic info of voter
        c.execute("SELECT basic_info_title, basic_info_value FROM basic_info WHERE voter_id ='{}'".format(id))
        basicInfoList = c.fetchall()

        # Gets basic info of voter
        c.execute("SELECT type, contact FROM contact WHERE voter_id ='{}'".format(id))
        contactList = c.fetchall()

        # Gets location of voter
        c.execute("SELECT address, address_title FROM location WHERE voter_id ='{}'".format(id))
        locationList = c.fetchall()

        # Gets education of voter
        c.execute("SELECT school FROM education WHERE voter_id ='{}'".format(id))
        educList = c.fetchall()

        # Gets work of voter
        c.execute("SELECT work_title, work_position FROM work WHERE voter_id ='{}'".format(id))
        workList = c.fetchall()

        # Gets relationship of voter
        c.execute("SELECT status FROM relationship WHERE voter_id ='{}'".format(id))
        relList = c.fetchall()

        # Gets family members of voter
        c.execute("SELECT name, relation FROM family_members WHERE voter_id ='{}'".format(id))
        famList = c.fetchall()

        # Gets pro skills of voter
        c.execute("SELECT skill FROM pro_skills WHERE voter_id ='{}'".format(id))
        proSkillsList = c.fetchall()


        return render_template('profile.html', name=name, basicInfoList=basicInfoList, contactList=contactList, fbId=fbId, locationList=locationList, educList=educList, workList=workList, relList=relList, famList=famList, proSkillsList=proSkillsList)
    return redirect(url_for('login'))

@app.route("/process")
def process():
    conn = sqlite3.connect('voters.db')
    c = conn.cursor()

    c.execute("SELECT id, full_name FROM voter")
    voterList = c.fetchall()

    vListConv = [{'value': i[0], 'label': i[1]} for i in voterList]

    pData = vListConv

    return json.dumps(pData)

    search = request.form['search']
    if search:
        newSearch = search

        return jsonify({'search': newSearch})
    return jsonify({'error': 'Missing Data!'})

@app.route("/mobile")
def about():
    if g.user:
        return render_template('m-input.html')
    else:
        return redirect(url_for('login'))

@app.route("/stats")
def stats():
    if g.user:
        conn = sqlite3.connect('voters.db')
        c = conn.cursor()

        # START DATA ANALYSIS FOR VOTER GENDERS
        c.execute("SELECT count(*) as maleCount FROM basic_info WHERE basic_info_value ='Male'")
        maleCount = c.fetchone()
        c.execute("SELECT count(*) as femaleCount FROM basic_info WHERE basic_info_value ='Female'")
        femaleCount = c.fetchone()
        totalCount = maleCount + femaleCount

        pie_chart = pygal.Pie()
        pie_chart.title = 'Catanduanes Voters by Gender %'
        pie_chart.add('Male', maleCount)
        pie_chart.add('Female', femaleCount)
        pie_chart.add('Total Voters', totalCount)
        pieGender = pie_chart.render(is_unicode=True)
        # END DATA ANALYSIS FOR VOTER GENDERS

        # START DATA ANALYSIS FOR VOTER EDUCATION
        c.execute("SELECT count(*) as csuCount FROM education WHERE school = 'Catanduanes State University'")
        csuCount = c.fetchone()
        c.execute("SELECT count(*) as otherCount FROM education WHERE school != 'Catanduanes State University'")
        otherCount = c.fetchone()

        line_chart = pygal.HorizontalBar()
        line_chart.title = 'Catanduanes Voters by Education %'
        line_chart.add('Catanduanes State University', csuCount)
        line_chart.add('Others', otherCount)
        lineEduc = line_chart.render(is_unicode=True)
        # END DATA ANALYSIS FOR VOTER EDUCATION

        # START DATA ANALYSIS FOR VOTER AGE
        c.execute("SELECT basic_info_value FROM basic_info WHERE basic_info_value < date('now') - 18")
        ageCount = c.fetchall()

        def calculate_age(dtob):
            today = date.today()
            return today.year - dtob.year - ((today.month, today.day) < (dtob.month, dtob.day))

        ageList = {18: 0, 19: 0, 20: 0, 21: 0, 22: 0, 23: 0, 24: 0, 25: 0, 26: 0, 27: 0, 28: 0, 29: 0, 'other': 0}

        i = 0
        while i < len(ageCount):
            birthday = ageCount[i][0]
            date_format = '%Y/%m/%d'
            try:
                tbirthday = datetime.strptime(birthday, date_format)

                ageNow = calculate_age(date(tbirthday.year, tbirthday.month, tbirthday.day))

                for x in range(18, 29):
                    if ageNow == x:
                        ageList[x] += 1
                    else:
                        ageList[x] += 0
            except:
                pass

            i += 1


        line_chart = pygal.Bar()
        line_chart.title = 'Catanduanes Voters by age %'
        line_chart.x_labels = map(str, range(18, 36))
        line_chart.add('Voters', [ageList[18], ageList[19], ageList[20], ageList[21], ageList[22], ageList[23], ageList[24], ageList[25], ageList[26], ageList[27], ageList[28], ageList[29]])
        lineAge = line_chart.render(is_unicode=True)
        # END DATA ANALYSIS FOR VOTER AGE

        return render_template('stats.html', pieGender=pieGender, lineEduc=lineEduc, lineAge=lineAge, ageNow=ageNow)
    return redirect(url_for('login'))

@app.route("/parseMobile", methods=['GET', 'POST'])
def parse():
    if g.user:
        conn = sqlite3.connect('voters.db')
        c = conn.cursor()


        #Facebook ID
        mSource2 = request.form['mSource2']
        pSoup = soup(mSource2, "html.parser")
        meta = pSoup.find("meta", {"property": "al:ios:url"})['content']

        c.execute("SELECT * FROM voter WHERE facebook_id ='{}'".format(meta))
        checkId = c.fetchall()

        if checkId:
            msg = 'User already exists!'

            mSource1 = request.form['mSource1']

            pageSoup = soup(mSource1, "html.parser")
            name = pageSoup.title.text
            # Education
            education = pageSoup.find("div", {"id": "education"})
            if education is not None:
                school = education.findAll("a", {"class": "_4e81"})
            else:
                school = ''

            # Work
            work = pageSoup.find("div", {"id": "work"})
            if work is not None:
                workTitle = work.findAll("a", {"class": "_4e81"})
                position = work.findAll("span", {"class": "_52jc _52ja"})
            else:
                workTitle = ''
                position = ''

            # Location
            address = pageSoup.findAll("div", {"class": "_4g34 _5b6q _5b6p _5i2i _52we"})
            if address is not None:
                addressTitle = pageSoup.findAll("h4", {"class": "_52jc _52ja _52jg"})
            else:
                addressTitle = ''

            # Basic Info
            basicInfo = pageSoup.find("div", {"id": "basic-info"})
            if basicInfo is not None:
                bIvalue = basicInfo.findAll("div", {"class": "_5cdv r"})
                bItitle = basicInfo.findAll("span", {"class": "_52jd _52ja _52jg"})
            else:
                bIvalue = ''
                bItitle = ''

            # Relationship
            relationship = pageSoup.find("div", {"id": "relationship"})
            if relationship is not None:
                relation = relationship.findAll("div", {"class": "_52ja _5cds _5cdt"})
            else:
                relation = ''

            # Professional Skills
            proSkills = pageSoup.find("div", {"id": "skills"})
            if proSkills is not None:
                pr = proSkills.findAll("div", {"class": "_5cds skills _2lcw _5cdt"})
            else:
                pr = ''

            # Family Members
            familyMembers = pageSoup.find("div", {"id": "family"})
            if familyMembers is not None:
                fMtitle = familyMembers.findAll("h3", {"class": "_52ja _52jg"})
                fMvalue = familyMembers.findAll("span", {"class": "_52jb"})
            else:
                fMvalue = ''
                fMtitle = ''

            # Contact Info
            contactInfo = pageSoup.find("div", {"id": "contact-info"})
            if contactInfo is not None:
                cIvalue = contactInfo.findAll("div", {"class": "_5cdv r"})
                cItitle = contactInfo.findAll("span", {"class": "_52jd _52ja _52jg"})
            else:
                cIvalue = ''
                cItitle = ''

        else:
            msg = 'Data gather was successful!'
            mSource1 = request.form['mSource1']

            pageSoup = soup(mSource1, "html.parser")
            name = pageSoup.title.text
            # Education
            education = pageSoup.find("div", {"id": "education"})
            if education is not None:
                school = education.findAll("a", {"class": "_4e81"})
            else:
                school = ''

            # Work
            work = pageSoup.find("div", {"id": "work"})
            if work is not None:
                workTitle = work.findAll("a", {"class": "_4e81"})
                position = work.findAll("span", {"class": "_52jc _52ja"})
            else:
                workTitle = ''
                position = ''

            # Location
            address = pageSoup.findAll("div", {"class": "_4g34 _5b6q _5b6p _5i2i _52we"})
            if address is not None:
                addressTitle = pageSoup.findAll("h4", {"class": "_52jc _52ja _52jg"})
            else:
                addressTitle = ''

            # Basic Info
            basicInfo = pageSoup.find("div", {"id": "basic-info"})
            if basicInfo is not None:
                bIvalue = basicInfo.findAll("div", {"class": "_5cdv r"})
                bItitle = basicInfo.findAll("span", {"class": "_52jd _52ja _52jg"})
            else:
                bIvalue = ''
                bItitle = ''

            # Relationship
            relationship = pageSoup.find("div", {"id": "relationship"})
            if relationship is not None:
                relation = relationship.findAll("div", {"class": "_52ja _5cds _5cdt"})
            else:
                relation = ''

            # Professional Skills
            proSkills = pageSoup.find("div", {"id": "skills"})
            if proSkills is not None:
                pr = proSkills.findAll("div", {"class": "_5cds skills _2lcw _5cdt"})
            else:
                pr = ''

            # Family Members
            familyMembers = pageSoup.find("div", {"id": "family"})
            if familyMembers is not None:
                fMtitle = familyMembers.findAll("h3", {"class": "_52ja _52jg"})
                fMvalue = familyMembers.findAll("span", {"class": "_52jb"})
            else:
                fMvalue = ''
                fMtitle = ''

            # Contact Info
            contactInfo = pageSoup.find("div", {"id":"contact-info"})
            if contactInfo is not None:
                cIvalue = contactInfo.findAll("div", {"class": "_5cdv r"})
                cItitle = contactInfo.findAll("span", {"class": "_52jd _52ja _52jg"})
            else:
                cIvalue = ''
                cItitle = ''


            # INSERT QUERY FOR name AND fb id
            c.execute("SELECT id FROM users WHERE username = '{}'".format(g.user))
            sysUserId = c.fetchone()[0]
            dateTime = time.strftime("%m/%d/%Y %H:%M:%S")
            c.execute("INSERT INTO voter ('full_name', 'facebook_id', 'dateRecorded', 'recordedBy') VALUES (?, ?, ?, ?);", (pageSoup.title.text, meta, dateTime, sysUserId))
            c.execute("SELECT id FROM voter WHERE facebook_id ='{}'".format(meta))
            id = c.fetchone()[0]


            # INSERT QUERY FOR education
            for s in school:
                c.execute("INSERT INTO education ('voter_id', 'school') VALUES (?, ?);", (id, s.text))
                conn.commit()

            # INSERT QUERY FOR work
            for w, p in zip(workTitle, position):
                c.execute("INSERT INTO work ('voter_id', 'work_title', 'work_position') VALUES (?, ?, ?);", (id, w.text, p.text))
                conn.commit()

            # INSERT QUERY FOR location
            for a, aT in zip(address, addressTitle):
                c.execute("INSERT INTO location ('voter_id', 'address_title', 'address') VALUES (?, ?, ?);", (id, a.h4.text, aT.text))
                conn.commit()

            # INSERT QUERY FOR basic info
            for bT, bV in zip(bItitle, bIvalue):
                if bT.text == 'Birthday':
                    try:
                        toFormatDate = datetime.strptime(bV.text, '%B %d, %Y')
                        formattedDate = toFormatDate.strftime('%Y/%m/%d')
                        c.execute("INSERT INTO basic_info ('voter_id', 'basic_info_title', 'basic_info_value') VALUES (?, ?, ?);",(id, bT.text, formattedDate))
                        conn.commit()
                    except:
                        toFormatDate = datetime.strptime(bV.text, '%B %d')
                        formattedDate = toFormatDate.strftime('%m/%d')
                        c.execute("INSERT INTO basic_info ('voter_id', 'basic_info_title', 'basic_info_value') VALUES (?, ?, ?);", (id, bT.text, formattedDate))
                        conn.commit()

                else:
                    c.execute("INSERT INTO basic_info ('voter_id', 'basic_info_title', 'basic_info_value') VALUES (?, ?, ?);", (id, bT.text, bV.text))
                    conn.commit()

            # INSERT QUERY FOR relationship
            for r in relation:
                c.execute("INSERT INTO relationship ('voter_id', 'status') VALUES (?, ?);", (id, r.text))
                conn.commit()

            # INSERT QUERY FOR pro skills
            for pS in pr:
                c.execute("INSERT INTO pro_skills ('voter_id', 'skill') VALUES (?, ?);", (id, pS.text))
                conn.commit()

            # INSERT QUERY FOR family members
            for fMt, fMv in zip(fMtitle, fMvalue):
                c.execute("INSERT INTO family_members ('voter_id', 'name', 'relation') VALUES (?, ?, ?);", (id, fMt.text, fMv.text))
                conn.commit()

            # INSERT QUERY FOR pro skills
            for cIv, cIt in zip(cIvalue, cItitle):
                c.execute("INSERT INTO contact ('voter_id', 'type', 'contact') VALUES (?, ?, ?);", (id, cIt.text, cIv.text))
                conn.commit()


        return render_template('m-input-show.html', cItitle=cItitle, cIvalue=cIvalue, fMtitle=fMtitle, fMvalue=fMvalue, checkId=checkId, school=school, name=name, workTitle=workTitle, position=position, address=address, addressTitle=addressTitle, bIvalue=bIvalue, bItitle=bItitle, relation=relation, pr=pr, meta=meta, msg=msg)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()