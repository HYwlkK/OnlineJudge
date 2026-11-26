<template>
  <div class="wrong-problems">
    <Panel shadow>
      <div slot="title">错题本</div>
      <div slot="extra">
        <Button icon="refresh" :loading="loading" @click="loadProblems">刷新</Button>
      </div>
      <p class="description">这里记录你在普通练习中做错的题目，同一道题只显示一次。点击题目可以重新练习。</p>
      <p v-if="error" class="error" role="alert">{{error}} 请点击刷新重试。</p>
      <p v-if="!isAuthenticated && !loading" class="description">请先登录后查看本人的错题。</p>
      <div v-if="isAuthenticated && !loading && !error && total === 0" class="empty" role="status">
        <Icon type="ios-book-outline" size="48"></Icon>
        <h3>暂无错题</h3>
        <p>在 OJ 中提交程序后，未通过的题目会自动出现在这里。</p>
        <Button type="primary" @click="goToProblems">去题库做题</Button>
      </div>
      <Table v-else-if="!error && (isAuthenticated || loading)" :columns="columns" :data="problems" :loading="loading" disabled-hover></Table>
      <div v-if="total > 0 && !error" class="pages">
        <Page :total="total" :current="page" :page-size="pageSize" show-total @on-change="changePage"></Page>
      </div>
    </Panel>
  </div>
</template>

<script>
  import {mapGetters} from 'vuex'
  import api from '@oj/api'

  const resultNames = {
    '-2': '编译错误',
    '-1': '答案错误',
    '0': '通过',
    '1': 'CPU 时间超限',
    '2': '实际运行时间超限',
    '3': '内存超限',
    '4': '运行错误',
    '5': '系统错误',
    '6': '等待判题',
    '7': '正在判题',
    '8': '部分通过'
  }

  export default {
    name: 'WrongProblemList',
    data () {
      return {
        loading: true,
        error: '',
        problems: [],
        total: 0,
        page: 1,
        pageSize: 20,
        requestVersion: 0,
        columns: [
          {title: '题号', key: '_id', width: 100},
          {
            title: '题目',
            minWidth: 220,
            render: (h, {row}) => h('router-link', {
              props: {to: {name: 'problem-details', params: {problemID: row._id}}},
              style: {whiteSpace: 'normal', wordBreak: 'break-word'}
            }, row.title)
          },
          {
            title: '难度',
            width: 90,
            render: (h, {row}) => h('span', {Low: '简单', Mid: '中等', High: '困难'}[row.difficulty] || row.difficulty)
          },
          {title: '失败次数', key: 'failure_count', width: 100},
          {
            title: '最近失败',
            minWidth: 150,
            render: (h, {row}) => h('router-link', {
              props: {to: {name: 'submission-details', params: {id: row.last_failure_submission_id}}}
            }, resultNames[String(row.last_failure_result)] || '未知结果')
          },
          {
            title: '最近提交结果',
            minWidth: 150,
            render: (h, {row}) => h('Tag', {
              props: {color: row.latest_result === 0 ? 'green' : 'blue'}
            }, resultNames[String(row.latest_result)] || '未知结果')
          },
          {
            title: '最近失败时间',
            minWidth: 175,
            render: (h, {row}) => h('span', new Date(row.last_failure_time).toLocaleString('zh-CN', {
              timeZone: 'Asia/Shanghai', hour12: false
            }))
          }
        ]
      }
    },
    computed: {
      ...mapGetters(['user', 'isAuthenticated']),
      currentUserID () {
        return this.user.id || null
      }
    },
    mounted () {
      this.loadProblems()
    },
    beforeDestroy () {
      this.requestVersion++
    },
    methods: {
      loadProblems () {
        const version = ++this.requestVersion
        const owner = this.currentUserID
        this.problems = []
        this.total = 0
        this.error = ''
        if (!owner) {
          this.loading = false
          return
        }
        this.loading = true
        api.getWrongProblemList((this.page - 1) * this.pageSize, this.pageSize).then(res => {
          if (version !== this.requestVersion || owner !== this.currentUserID) return
          const data = res.data.data
          if (this.page > 1 && data.results.length === 0) {
            this.page = Math.max(1, Math.ceil(data.total / this.pageSize))
            this.loadProblems()
            return
          }
          this.problems = data.results
          this.total = data.total
          this.loading = false
        }, () => {
          if (version !== this.requestVersion || owner !== this.currentUserID) return
          this.error = '错题列表加载失败。'
          this.loading = false
        })
      },
      changePage (page) {
        this.page = page
        this.loadProblems()
      },
      goToProblems () {
        this.$router.push({name: 'problem-list'})
      }
    },
    watch: {
      currentUserID () {
        this.page = 1
        this.loadProblems()
      }
    }
  }
</script>

<style lang="less" scoped>
  .wrong-problems {
    .description {margin-bottom: 20px; color: #657180; line-height: 1.8;}
    .error {padding: 24px; color: #d45645;}
    .empty {
      text-align: center;
      padding: 48px 16px;
      color: #657180;
      h3 {margin: 16px 0 8px; color: #495060; font-size: 20px;}
      p {margin-bottom: 22px;}
    }
    .pages {margin-top: 24px; text-align: right;}
  }
</style>
